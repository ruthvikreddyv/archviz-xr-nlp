import base64, os, shutil
from collections import defaultdict
import cv2, fitz, numpy as np, pytesseract
from PIL import Image

def configure_tesseract():
    candidates=[os.getenv("TESSERACT_CMD"),shutil.which("tesseract"),
                r"C:\Program Files\Tesseract-OCR\tesseract.exe"]
    for c in candidates:
        if c and os.path.exists(c):
            pytesseract.pytesseract.tesseract_cmd=c; return c
    return None

def _resize_if_small(img):
    h,w=img.shape[:2]
    if w<1200:
        scale=max(2.0,1200/w); img=cv2.resize(img,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    return img

def _deskew(gray):
    edges=cv2.Canny(gray,50,150,apertureSize=3)
    lines=cv2.HoughLines(edges,1,np.pi/180,threshold=100)
    if lines is None: return gray
    angles=[np.degrees(t)-90 for _,t in lines[:,0] if -10<np.degrees(t)-90<10]
    if not angles: return gray
    angle=float(np.median(angles))
    if abs(angle)<0.3: return gray
    h,w=gray.shape[:2]; M=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0)
    return cv2.warpAffine(gray,M,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)

def _channel_ocr_passes(img, psm):
    config=f"--psm {psm} --oem 3"; results=[]
    def _ocr(ch,label):
        raw=pytesseract.image_to_string(ch,config=config)
        words=[w for w in raw.split() if len(w)>=2]
        results.append((raw,len(words),label))
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); gray=_deskew(gray)
    denoised=cv2.fastNlMeansDenoising(gray,h=10)
    _,otsu=cv2.threshold(denoised,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); _ocr(otsu,"otsu")
    for ch_idx,ch_name in enumerate([2,1,0]):
        ch=img[:,:,ch_name]; _,ct=cv2.threshold(ch,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); _ocr(ct,f"ch{ch_idx}")
    adaptive=cv2.adaptiveThreshold(denoised,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,15,3); _ocr(adaptive,"adaptive")
    clahe=cv2.createCLAHE(clipLimit=2.0,tileGridSize=(8,8)); eq=clahe.apply(denoised)
    _,eq_t=cv2.threshold(eq,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU); _ocr(eq_t,"clahe")
    return results

def preprocess_and_ocr(path):
    img=cv2.imread(path)
    if img is None: raise FileNotFoundError(f"Cannot load image: {path}")
    img=_resize_if_small(img); h,w=img.shape[:2]; psm=11 if w>h else 6
    passes=_channel_ocr_passes(img,psm)
    best_text,best_count,best_label=max(passes,key=lambda t:t[1])
    print(f"[OCR] Best pass: {best_label} → {best_count} words")
    merged=[]; seen=set()
    for raw,count,_ in sorted(passes,key=lambda t:t[1],reverse=True):
        if count<max(best_count*0.4,2): continue
        for word in raw.split():
            wl=word.lower()
            if wl not in seen and len(word)>=2: seen.add(wl); merged.append(word)
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); gray=_deskew(gray)
    denoised=cv2.fastNlMeansDenoising(gray,h=10)
    _,thresh=cv2.threshold(denoised,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    return " ".join(merged), _extract_layout_blocks(thresh)

def _extract_layout_blocks(processed):
    config="--psm 11 --oem 3"; data=pytesseract.image_to_data(processed,output_type=pytesseract.Output.DICT,config=config)
    ih,iw=processed.shape[:2]; lines=defaultdict(list)
    for i,text in enumerate(data["text"]):
        text=text.strip()
        if not text or len(text)<2 or int(data["conf"][i])<20: continue
        key=(data["page_num"][i],data["block_num"][i],data["par_num"][i],data["line_num"][i])
        lines[key].append({"text":text,"left":data["left"][i],"top":data["top"][i],"width":data["width"][i],"height":data["height"][i],"image_width":iw,"image_height":ih,"conf":int(data["conf"][i])})
    blocks=[]
    for words in lines.values():
        l=min(w["left"] for w in words); t=min(w["top"] for w in words)
        r=max(w["left"]+w["width"] for w in words); b=max(w["top"]+w["height"] for w in words)
        blocks.append({"text":" ".join(w["text"] for w in words),"left":l,"top":t,"width":r-l,"height":b-t,"image_width":iw,"image_height":ih})
        blocks.extend(words)
    return blocks

def pdf_has_text_layer(path):
    doc=fitz.open(path); total=sum(len(p.get_text().strip()) for p in doc); doc.close(); return total>=20

def extract_from_pdf(path):
    if not os.path.exists(path): raise FileNotFoundError(f"PDF not found: {path}")
    doc=fitz.open(path); pages=[p.get_text().strip() for p in doc if p.get_text().strip()]; doc.close()
    return " ".join(pages)

def rasterize_pdf_page(path,page_num=0,dpi=200):
    doc=fitz.open(path); page=doc[page_num]; mat=fitz.Matrix(dpi/72,dpi/72)
    pix=page.get_pixmap(matrix=mat,colorspace=fitz.csRGB); data=pix.tobytes("png"); doc.close(); return data

def rasterize_pdf_page_as_cv2(path,page_num=0,dpi=200):
    return cv2.imdecode(np.frombuffer(rasterize_pdf_page(path,page_num,dpi),np.uint8),cv2.IMREAD_COLOR)

def pdf_page_to_base64(path,page_num=0,dpi=200):
    return base64.b64encode(rasterize_pdf_page(path,page_num,dpi)).decode()

def image_file_to_base64(path):
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode()

def extract_with_layout(path):
    ext=os.path.splitext(path)[1].lower()
    if ext==".pdf":
        if pdf_has_text_layer(path):
            print("[OCR] Text-layer PDF"); return {"text":extract_from_pdf(path),"layout_blocks":[],"is_scanned":False}
        else:
            print("[OCR] Scanned PDF — rasterising for OCR")
            if not configure_tesseract(): raise ValueError("Tesseract required for scanned PDFs")
            img=rasterize_pdf_page_as_cv2(path,dpi=200)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png",delete=False) as tmp:
                cv2.imwrite(tmp.name,img); tmp_path=tmp.name
            try: text,blocks=preprocess_and_ocr(tmp_path)
            finally: os.unlink(tmp_path)
            return {"text":text,"layout_blocks":blocks,"is_scanned":True}
    elif ext in {".png",".jpg",".jpeg",".bmp",".tiff"}:
        if not configure_tesseract(): raise ValueError("Tesseract not found")
        print("[OCR] Image — multi-channel OCR")
        text,blocks=preprocess_and_ocr(path)
        return {"text":text,"layout_blocks":blocks,"is_scanned":False}
    else: raise ValueError(f"Unsupported: {ext}")

def extract(path):
    r=extract_with_layout(path); text=r["text"]
    if not text.strip(): raise ValueError("No text extracted")
    print(f"[OCR] {len(text.split())} words"); return text