import json, os, pytest, numpy as np

def make_entities(*labels):
    return [{"id":l.lower().replace(" ","_"),"label":l,"type":"component"} for l in labels]

def make_relations(pairs):
    return [{"from":a,"to":b,"label":"feeds"} for a,b in pairs]

class TestOCR:
    def test_clean_ocr_text(self):
        from pipeline.ocr import extract_with_layout
        assert callable(extract_with_layout)

    def test_pdf_has_text_layer_false(self,tmp_path):
        import fitz
        doc=fitz.open(); doc.new_page(); p=str(tmp_path/"e.pdf"); doc.save(p); doc.close()
        from pipeline.ocr import pdf_has_text_layer
        assert pdf_has_text_layer(p) is False

    def test_pdf_has_text_layer_true(self,tmp_path):
        import fitz
        doc=fitz.open(); page=doc.new_page(); page.insert_text((72,72),"Encoder Decoder Attention Multi-Head Feed Forward")
        p=str(tmp_path/"t.pdf"); doc.save(p); doc.close()
        from pipeline.ocr import pdf_has_text_layer
        assert pdf_has_text_layer(p) is True

    def test_rasterize_returns_png(self,tmp_path):
        import fitz
        doc=fitz.open(); doc.new_page(); p=str(tmp_path/"p.pdf"); doc.save(p); doc.close()
        from pipeline.ocr import rasterize_pdf_page
        data=rasterize_pdf_page(p,dpi=72)
        assert data[:4]==b"\x89PNG"

class TestNER:
    def test_valid_entity_allows_allowlist(self):
        from pipeline.ner import is_valid_entity
        assert is_valid_entity("ffn")
        assert is_valid_entity("mha")
        assert is_valid_entity("gru")

    def test_valid_entity_rejects_digits(self):
        from pipeline.ner import is_valid_entity
        assert not is_valid_entity("123")

    def test_valid_entity_rejects_articles(self):
        from pipeline.ner import is_valid_entity
        assert not is_valid_entity("the")

    def test_max_edges_per_source_is_10(self):
        from pipeline.ner import deduplicate_and_limit, MAX_EDGES_PER_SOURCE
        assert MAX_EDGES_PER_SOURCE==10
        rels=[{"from":"enc","to":f"n{i}","label":"feeds"} for i in range(15)]
        r=deduplicate_and_limit(rels)
        from collections import Counter
        counts=Counter(x["from"] for x in r)
        assert counts["enc"]==10

    def test_extract_returns_keys(self):
        from pipeline.ner import extract
        r=extract("The encoder processes tokens. The decoder generates output embeddings.")
        assert "entities" in r and "relations" in r

    def test_extract_raises_on_empty(self):
        from pipeline.ner import extract
        with pytest.raises(ValueError): extract("   ")

class TestGraph:
    def test_no_proximity_fallback_when_edges_present(self):
        from pipeline.graph import build_graph
        G=build_graph(make_entities("Encoder","Decoder","Attention"),
                      [{"from":"encoder","to":"decoder","label":"feeds"}])
        assert G.number_of_edges()==1

    def test_empty_relations_gives_zero_edges(self):
        from pipeline.graph import build_graph
        G=build_graph(make_entities("A","B","C","D"),[])
        assert G.number_of_edges()==0

    def test_cycle_detection(self):
        from pipeline.graph import build_graph, has_cycles
        G=build_graph([{"id":"a","label":"A","type":"component"},{"id":"b","label":"B","type":"component"}],
                      [{"from":"a","to":"b","label":"f"},{"from":"b","to":"a","label":"f"}])
        assert has_cycles(G)

    def test_get_stats(self):
        from pipeline.graph import build_graph, get_stats
        G=build_graph(make_entities("A","B"),[{"from":"a","to":"b","label":"feeds"}])
        s=get_stats(G)
        assert s["total_edges"]==1

class TestGraphCleaner:
    def test_clean_label_merged_rejected(self):
        from pipeline.graph_cleaner import clean_label
        assert clean_label("Input Tokens Output Tokens Decoder Encoder") is None

    def test_clean_label_known_alias(self):
        from pipeline.graph_cleaner import clean_label
        assert clean_label("Norm")=="Normalization"

    def test_clean_label_noise_rejected(self):
        from pipeline.graph_cleaner import clean_label
        assert clean_label(") ~ Ge") is None

    def test_clean_graph_removes_dangling(self):
        from pipeline.graph_cleaner import clean_graph
        c={"nodes":[{"id":"enc","label":"Encoder","type":"component"},{"id":"bad","label":") ~ Ge","type":"component"}],
           "edges":[{"from":"enc","to":"bad","label":"feeds"}],"quiz":[]}
        cleaned=clean_graph(c)
        ids={n["id"] for n in cleaned["nodes"]}
        assert "bad" not in ids
        assert all(e["from"] in ids and e["to"] in ids for e in cleaned["edges"])

class TestSpatial:
    def test_spring_layout_in_range(self):
        from pipeline.graph import build_graph
        from pipeline.spatial import map_spatial_coords, graph_to_contract_nodes
        G=build_graph(make_entities("A","B","C"),make_relations([("a","b"),("b","c")]))
        G=map_spatial_coords(G)
        for n in graph_to_contract_nodes(G):
            assert -5<=n["x"]<=5 and -5<=n["y"]<=5

    def test_hierarchical_layout(self):
        from pipeline.graph import build_graph
        from pipeline.spatial import map_hierarchical_coords, graph_to_contract_nodes
        G=build_graph(make_entities("In","Enc","Dec","Out"),
                      make_relations([("in","enc"),("enc","dec"),("dec","out")]))
        G=map_hierarchical_coords(G)
        nodes=graph_to_contract_nodes(G)
        assert len(nodes)==4
        ys=[n["y"] for n in nodes]
        assert len(set(ys))>1

class TestLLM:
    def test_make_id(self):
        from pipeline.llm import make_id
        assert make_id("Multi-Head Attention")=="multi_head_attention"
        assert make_id("Add & Norm")=="add_norm"
        assert make_id("   ")=="concept"

    def test_is_supported_label_strict(self):
        from pipeline.llm import is_supported_label
        ents=[{"label":"Encoder"},{"label":"Decoder"}]
        assert is_supported_label("Encoder Stack",ents)
        assert not is_supported_label("Convolutional Feature Map",ents)

    def test_fallback_no_proximity_edges(self):
        from pipeline.llm import fallback_result
        r=fallback_result(make_entities("A","B","C","D"),[])
        assert r["edges"]==[]

    def test_generate_raises_on_empty(self):
        from pipeline.llm import generate
        with pytest.raises(ValueError): generate([],[])

class TestContractSchema:
    CONTRACT={"nodes":[{"id":"enc","label":"Encoder","type":"component","x":0.1,"y":0.5,"z":-0.3},
                       {"id":"dec","label":"Decoder","type":"component","x":-0.2,"y":-0.5,"z":0.1}],
              "edges":[{"from":"enc","to":"dec","label":"feeds"}],
              "explanation":"Encoder-decoder architecture.",
              "quiz":[{"q":"What does the encoder do?","options":["Encode","Decode","Attend","Norm"],"answer":0}]}

    def test_nodes_have_required_fields(self):
        for n in self.CONTRACT["nodes"]:
            for f in ["id","label","type","x","y","z"]: assert f in n

    def test_edges_reference_valid_nodes(self):
        ids={n["id"] for n in self.CONTRACT["nodes"]}
        for e in self.CONTRACT["edges"]:
            assert e["from"] in ids and e["to"] in ids

    def test_quiz_structure(self):
        for q in self.CONTRACT["quiz"]:
            assert len(q["options"])==4 and 0<=q["answer"]<=3

    def test_contract_serialisable(self):
        json.dumps(self.CONTRACT)