from __future__ import annotations
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class QuizAttempt:
    question: str; topic: str; correct: bool; round_n: int

@dataclass
class LearnerSession:
    session_id: str
    attempts: list[QuizAttempt] = field(default_factory=list)
    round_number: int = 0

    def overall_score(self):
        if not self.attempts: return 50.0
        return 100.0*sum(1 for a in self.attempts if a.correct)/len(self.attempts)

    def recent_score(self,last_n=5):
        r=self.attempts[-last_n:] if len(self.attempts)>=last_n else self.attempts
        if not r: return 50.0
        return 100.0*sum(1 for a in r if a.correct)/len(r)

    def weak_topics(self,threshold=0.5):
        ts=defaultdict(list)
        for a in self.attempts:
            if a.topic: ts[a.topic].append(a.correct)
        weak=[(t,sum(v)/len(v)) for t,v in ts.items() if len(v)>=2 and sum(v)/len(v)<threshold]
        return [t for t,_ in sorted(weak,key=lambda x:x[1])]

    def next_suggested_topic(self,all_topics):
        weak=self.weak_topics()
        if weak: return weak[0]
        attempted={a.topic for a in self.attempts}
        for t in all_topics:
            if t not in attempted: return t
        return all_topics[0] if all_topics else None

_store={}; _lock=threading.Lock()

def _get(sid):
    with _lock:
        if sid not in _store: _store[sid]=LearnerSession(session_id=sid)
        return _store[sid]

def record_quiz_result(session_id,question,topic,correct):
    s=_get(session_id)
    with _lock: s.attempts.append(QuizAttempt(question=question,topic=topic,correct=correct,round_n=s.round_number))

def end_round(session_id):
    s=_get(session_id)
    with _lock: s.round_number+=1

def get_learning_level(session_id,all_topics=None):
    s=_get(session_id); score=s.recent_score(5); weak=s.weak_topics(); topics=all_topics or []
    next_t=s.next_suggested_topic(topics)
    if score<40: level,diff,hints,hb="beginner","easy",True,3
    elif score<70: level,diff,hints,hb="intermediate","medium",False,1
    else: level,diff,hints,hb="advanced","hard",False,0
    return {"level":level,"difficulty":diff,"hints":hints,"hint_budget":hb,
            "next_topic":next_t or (topics[0] if topics else ""),"score":round(score,1),"weak_topics":weak[:3]}

def calculate_score(quiz,answers):
    if not quiz or len(answers)<len(quiz): return 0.0
    return round(100.0*sum(1 for i,q in enumerate(quiz) if answers[i]==q.get("answer",-1))/len(quiz),1)

def reset_session(session_id):
    with _lock: _store.pop(session_id,None)