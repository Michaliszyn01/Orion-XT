import json
import re
from datetime import datetime

from core.utils import normalize_text


SUBJECT_KEYWORDS = {
    "matematica": ["matematica", "matemática"],
    "portugues": ["portugues", "português"],
    "biologia": ["biologia"],
    "fisica": ["fisica", "física"],
    "quimica": ["quimica", "química"],
    "historia": ["historia", "história"],
    "geografia": ["geografia"],
    "redacao": ["redacao", "redação"],
    "ingles": ["ingles", "inglês"],
    "filosofia": ["filosofia"],
    "sociologia": ["sociologia"],
}

SUBJECT_LABELS = {
    "matematica": "matemática",
    "portugues": "português",
    "biologia": "biologia",
    "fisica": "física",
    "quimica": "química",
    "historia": "história",
    "geografia": "geografia",
    "redacao": "redação",
    "ingles": "inglês",
    "filosofia": "filosofia",
    "sociologia": "sociologia",
}

AREA_ALIASES = {
    "matematica": ["matematica", "matemática", "mat"],
    "redacao": ["redacao", "redação"],
    "linguagens": ["linguagens", "portugues", "português"],
    "natureza": [
        "natureza",
        "ciencias da natureza",
        "ciências da natureza",
        "biologia",
        "fisica",
        "física",
        "quimica",
        "química",
    ],
    "humanas": [
        "humanas",
        "ciencias humanas",
        "ciências humanas",
        "historia",
        "história",
        "geografia",
        "filosofia",
        "sociologia",
    ],
}

AREA_LABELS = {
    "matematica": "matemática",
    "redacao": "redação",
    "linguagens": "linguagens",
    "natureza": "natureza",
    "humanas": "humanas",
}

UNIVERSITY_ALIASES = ["ufpr", "utfpr"]


class ContextEngine:
    def __init__(self, memory_store):
        self.memory_store = memory_store
        self.current_context = {
            "area": "",
            "subject": "",
            "topic": "",
            "difficulty": "",
            "learning": "",
            "active": False,
        }
        self.academic_context = {
            "enem_score": "",
            "enem_target": "",
            "area_scores": {},
            "target_course": "",
            "target_university": "",
        }
        self._load_context_from_memory()

    def _load_context_from_memory(self):
        if self.memory_store is None:
            return

        try:
            memories = self.memory_store.get_relevant_memories(category="study", limit=10)
        except Exception as exc:
            print("Erro ao carregar contexto de estudo:", repr(exc))
            memories = []

        active_value = None

        for memory in memories:
            key = memory.get("key") or memory.get("memory_key") or memory.get("name")
            value = memory.get("value") or memory.get("content") or ""
            metadata = self._decode_metadata(memory.get("metadata") or memory.get("meta"))

            if key == "current_focus" and value:
                subject = metadata.get("subject_display") or metadata.get("subject") or ""
                topic = metadata.get("topic_display") or metadata.get("topic") or ""

                if not topic:
                    subject, topic = self._split_focus_value(value)

                self.current_context["area"] = "estudo"
                self.current_context["subject"] = subject
                self.current_context["topic"] = topic
                self.current_context["active"] = True

            if key == "last_difficulty" and value:
                self.current_context["area"] = "estudo"
                self.current_context["difficulty"] = value

            if key == "last_learning" and value:
                self.current_context["area"] = "estudo"
                self.current_context["learning"] = value

            if key == "study_active":
                active_value = normalize_text(value)

        if active_value is not None:
            self.current_context["active"] = active_value == "true"

        self._load_academic_context_from_memory()

    def _load_academic_context_from_memory(self):
        if self.memory_store is None:
            return

        categories = ["enem", "enem_area_scores", "academic_goal"]

        for category in categories:
            try:
                memories = self.memory_store.get_relevant_memories(category=category, limit=20)
            except Exception as exc:
                print("Erro ao carregar contexto academico:", repr(exc))
                continue

            for memory in memories:
                key = memory.get("key") or memory.get("memory_key") or memory.get("name")
                value = memory.get("value") or memory.get("content") or ""

                if category == "enem" and key == "last_score":
                    self.academic_context["enem_score"] = value

                if category == "enem" and key == "target_score":
                    self.academic_context["enem_target"] = value

                if category == "enem_area_scores" and key and value:
                    self.academic_context["area_scores"][key] = value

                if category == "academic_goal" and key == "target_course":
                    self.academic_context["target_course"] = value

                if category == "academic_goal" and key == "target_university":
                    self.academic_context["target_university"] = value

    def analyze(self, text: str) -> dict:
        normalized = normalize_text(text).strip(" .?!,;:-")
        display_text = self._display_text(text)

        if not normalized:
            return {"intent": "none"}

        if self._is_enem_strategy_question(normalized):
            return {"intent": "ask_enem_strategy"}

        target_score = self._extract_enem_target_score(normalized)
        if target_score is not None:
            return {
                "intent": "register_enem_target",
                "exam": "enem",
                "target_score": target_score,
            }

        area_score = self._extract_area_score(normalized)
        if area_score:
            return {
                "intent": "register_area_score",
                "area": area_score["area"],
                "score": area_score["score"],
            }

        enem_score = self._extract_enem_score(normalized)
        if enem_score is not None:
            return {
                "intent": "register_enem_score",
                "exam": "enem",
                "score": enem_score,
            }

        academic_goal = self._extract_academic_goal(normalized, display_text)
        if academic_goal.get("course"):
            return {
                "intent": "register_target_course",
                **academic_goal,
            }

        if academic_goal.get("university"):
            return {
                "intent": "register_target_university",
                "university": academic_goal["university"],
            }

        if self._is_current_context_question(normalized):
            return {"intent": "ask_current_context"}

        if self._is_next_step_question(normalized):
            return {"intent": "ask_next_step"}

        if self._is_end_study_session(normalized):
            return {"intent": "end_study_session"}

        if self._is_explain_current_context_request(normalized):
            return {"intent": "explain_current_context"}

        difficulty = self._extract_difficulty(normalized)
        if difficulty:
            return {
                "intent": "register_difficulty",
                "difficulty": difficulty,
            }

        learning = self._extract_learning(normalized)
        if learning:
            return {
                "intent": "register_learning",
                "learning": learning,
            }

        study_target = self._extract_study_target(normalized)
        if study_target:
            display_target = self._extract_study_target_display(display_text)
            subject = self._detect_subject(study_target)
            topic = self._extract_topic(study_target, subject)
            subject_display = SUBJECT_LABELS.get(subject, subject)
            topic_display = self._extract_topic_display(display_target, subject)

            return {
                "intent": "start_study_session",
                "area": "estudo",
                "subject": subject,
                "topic": topic,
                "subject_display": subject_display,
                "topic_display": topic_display,
            }

        return {"intent": "none"}

    def handle(self, text: str) -> str | None:
        data = self.analyze(text)
        intent = data.get("intent")

        if intent == "none":
            return None

        if intent == "register_enem_score":
            return self._handle_register_enem_score(data)

        if intent == "register_enem_target":
            return self._handle_register_enem_target(data)

        if intent == "register_area_score":
            return self._handle_register_area_score(data)

        if intent == "register_target_course":
            return self._handle_register_target_course(data)

        if intent == "register_target_university":
            return self._handle_register_target_university(data)

        if intent == "ask_enem_strategy":
            return self._handle_ask_enem_strategy(data)

        if intent == "start_study_session":
            return self._handle_start_study_session(data)

        if intent == "register_difficulty":
            return self._handle_register_difficulty(data)

        if intent == "register_learning":
            return self._handle_register_learning(data)

        if intent == "ask_current_context":
            return self._handle_ask_current_context(data)

        if intent == "ask_next_step":
            return self._handle_ask_next_step(data)

        if intent == "explain_current_context":
            return self._handle_explain_current_context(data)

        if intent == "end_study_session":
            return self._handle_end_study_session(data)

        return None

    def _handle_register_enem_score(self, data: dict) -> str:
        score = data.get("score")
        metadata = self._metadata(data)
        self.academic_context["enem_score"] = str(score)

        self._safe_save(
            "save_event",
            event_type="enem_score",
            content=f"Pontuação ENEM registrada: {score}",
            importance=4,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="enem",
            key="last_score",
            value=str(score),
            importance=4,
            metadata=metadata,
        )

        return f"Entendido. Registrei sua pontuação do ENEM como {score}."

    def _handle_register_enem_target(self, data: dict) -> str:
        target_score = data.get("target_score")
        metadata = self._metadata(data)
        self.academic_context["enem_target"] = str(target_score)

        self._safe_save(
            "save_event",
            event_type="enem_target",
            content=f"Meta ENEM registrada: {target_score}",
            importance=4,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="enem",
            key="target_score",
            value=str(target_score),
            importance=4,
            metadata=metadata,
        )

        return f"Meta registrada. Seu objetivo agora é chegar em {target_score} no ENEM."

    def _handle_register_area_score(self, data: dict) -> str:
        area = data.get("area", "")
        score = data.get("score")
        label = AREA_LABELS.get(area, area)
        metadata = self._metadata(data)
        self.academic_context["area_scores"][area] = str(score)

        self._safe_save(
            "save_event",
            event_type="enem_area_score",
            content=f"Nota de {label} registrada: {score}",
            importance=4,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="enem_area_scores",
            key=area,
            value=str(score),
            importance=4,
            metadata=metadata,
        )

        return f"Registrei sua nota em {label} como {score}."

    def _handle_register_target_course(self, data: dict) -> str:
        course = data.get("course", "")
        university = data.get("university", "")
        metadata = self._metadata(data)
        course_label = self._format_course_name(course)

        self.academic_context["target_course"] = course
        self._safe_save(
            "save_event",
            event_type="target_course",
            content=f"Curso alvo registrado: {course}",
            importance=4,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="academic_goal",
            key="target_course",
            value=course,
            importance=4,
            metadata=metadata,
        )

        if university:
            university = university.lower()
            university_label = university.upper()
            self.academic_context["target_university"] = university
            self._safe_save(
                "save_long_memory",
                category="academic_goal",
                key="target_university",
                value=university,
                importance=4,
                metadata=metadata,
            )
            return (
                f"Entendido. Registrei {course_label} como seu curso alvo "
                f"e {university_label} como sua universidade alvo."
            )

        return f"Entendido. Registrei {course_label} como seu curso alvo."

    def _handle_register_target_university(self, data: dict) -> str:
        university = data.get("university", "").lower()
        university_label = university.upper()
        metadata = self._metadata(data)
        self.academic_context["target_university"] = university

        self._safe_save(
            "save_event",
            event_type="target_university",
            content=f"Universidade alvo registrada: {university}",
            importance=4,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="academic_goal",
            key="target_university",
            value=university,
            importance=4,
            metadata=metadata,
        )

        return f"Entendido. Registrei {university_label} como sua universidade alvo."

    def _handle_ask_enem_strategy(self, data: dict) -> str:
        self._safe_save(
            "save_event",
            event_type="enem_strategy_query",
            content="Usuario pediu estrategia para o ENEM",
            importance=2,
            metadata=self._metadata({
                **data,
                "academic_context": dict(self.academic_context),
            }),
        )

        return self._build_enem_strategy_response()

    def _handle_start_study_session(self, data: dict) -> str:
        subject = data.get("subject_display") or data.get("subject", "")
        topic = data.get("topic_display") or data.get("topic", "")
        metadata = self._metadata(data)
        focus_text = self._format_focus(subject, topic)
        focus_value = self._storage_focus(data.get("subject", ""), data.get("topic", "")) or focus_text
        storage_focus = focus_text or focus_value

        self.current_context.update({
            "area": "estudo",
            "subject": subject,
            "topic": topic,
            "active": True,
        })

        self._safe_save(
            "save_event",
            event_type="study_start",
            content=f"Inicio de estudo: {storage_focus}",
            importance=2,
            metadata=metadata,
        )
        self._safe_save(
            "save_short_memory",
            category="study_context",
            content=f"Foco atual: {storage_focus}",
            importance=2,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="study",
            key="current_focus",
            value=focus_value,
            importance=2,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="study",
            key="study_active",
            value="true",
            importance=1,
            metadata=metadata,
        )

        if focus_text:
            return f"Entendido. Seu foco de estudo agora é {focus_text}."

        return "Entendido. Vamos estudar."

    def _handle_register_difficulty(self, data: dict) -> str:
        difficulty = data.get("difficulty", "")
        metadata = self._metadata(data)
        self.current_context["area"] = "estudo"
        self.current_context["difficulty"] = difficulty

        self._safe_save(
            "save_event",
            event_type="study_difficulty",
            content=f"Dificuldade registrada: {difficulty}",
            importance=3,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="study",
            key="last_difficulty",
            value=difficulty,
            importance=3,
            metadata=metadata,
        )

        return "Registrei essa dificuldade no seu contexto de estudo atual."

    def _handle_register_learning(self, data: dict) -> str:
        learning = data.get("learning", "")
        metadata = self._metadata(data)
        self.current_context["area"] = "estudo"
        self.current_context["learning"] = learning

        self._safe_save(
            "save_event",
            event_type="study_learning",
            content=f"Aprendizado registrado: {learning}",
            importance=2,
            metadata=metadata,
        )
        self._safe_save(
            "save_long_memory",
            category="study",
            key="last_learning",
            value=learning,
            importance=2,
            metadata=metadata,
        )

        return "Boa. Registrei esse aprendizado no seu progresso de estudo."

    def _handle_ask_current_context(self, data: dict) -> str:
        self._safe_save(
            "save_event",
            event_type="study_context_query",
            content="Usuario perguntou pelo contexto atual de estudo",
            importance=1,
            metadata=self._metadata(data),
        )

        focus_text = self._format_focus(
            self.current_context.get("subject", ""),
            self.current_context.get("topic", ""),
        )

        if not focus_text:
            return "Ainda não tenho um foco de estudo registrado."

        if not self.current_context.get("active"):
            return f"Sua última sessão de estudo foi sobre {focus_text}."

        return f"Seu foco atual de estudo é {focus_text}."

    def _handle_ask_next_step(self, data: dict) -> str:
        self._safe_save(
            "save_event",
            event_type="study_next_step",
            content="Usuario pediu o proximo passo de estudo",
            importance=1,
            metadata=self._metadata(data),
        )

        if self.current_context.get("difficulty"):
            return (
                "Pelo seu contexto atual, recomendo revisar sua dificuldade "
                "principal e depois fazer questões sobre o tema."
            )

        return "Recomendo começar com uma revisão curta do tema e depois resolver algumas questões."

    def _handle_explain_current_context(self, data: dict) -> str | None:
        if not self.current_context.get("active"):
            return None

        topic = self.current_context.get("topic", "")
        self._safe_save(
            "save_event",
            event_type="study_explanation",
            content=f"Explicacao solicitada sobre: {topic}",
            importance=2,
            metadata=self._metadata({
                **data,
                "context": dict(self.current_context),
            }),
        )

        return self._explain_current_context()

    def _handle_end_study_session(self, data: dict) -> str:
        focus_text = self._format_focus(
            self.current_context.get("subject", ""),
            self.current_context.get("topic", ""),
        )
        metadata = self._metadata({
            **data,
            "context": dict(self.current_context),
        })

        self._safe_save(
            "save_event",
            event_type="study_end",
            content=f"Fim de estudo: {focus_text or 'sem foco ativo'}",
            importance=2,
            metadata=metadata,
        )
        self._safe_save(
            "save_short_memory",
            category="study_context",
            content=f"Sessao encerrada: {focus_text or 'sem foco ativo'}",
            importance=1,
            metadata=metadata,
        )

        self.current_context["active"] = False
        self._safe_save(
            "save_long_memory",
            category="study",
            key="study_active",
            value="false",
            importance=1,
            metadata=dict(self.current_context),
        )
        return "Sessão de estudo encerrada. Registrei o contexto atual."

    def _extract_enem_score(self, text: str) -> int | None:
        if "enem" not in text:
            return None

        if not any(phrase in text for phrase in ["tirei", "fiz", "minha nota", "nota no enem", "nota do enem"]):
            return None

        return self._extract_score(text, min_score=300, max_score=1000)

    def _extract_enem_target_score(self, text: str) -> int | None:
        target_markers = [
            "quero chegar em",
            "minha meta e",
            "minha meta eh",
            "quero tirar",
        ]

        if not any(marker in text for marker in target_markers):
            return None

        if "enem" not in text and "meta" not in text:
            return None

        return self._extract_score(text, min_score=300, max_score=1000)

    def _extract_area_score(self, text: str) -> dict | None:
        area = self._detect_area(text)

        if not area:
            return None

        score = self._extract_score(text, min_score=0, max_score=1000)

        if score is None:
            return None

        return {
            "area": area,
            "score": score,
        }

    def _extract_score(self, text: str, min_score: int = 0, max_score: int = 1000) -> int | None:
        for match in re.finditer(r"\b\d{1,4}\b", text):
            score = int(match.group(0))

            if min_score <= score <= max_score:
                return score

        return None

    def _detect_area(self, text: str) -> str:
        for area, aliases in AREA_ALIASES.items():
            normalized_aliases = sorted(
                [normalize_text(alias) for alias in aliases],
                key=len,
                reverse=True,
            )

            for alias in normalized_aliases:
                if re.search(rf"\b{re.escape(alias)}\b", text):
                    return area

        return ""

    def _extract_academic_goal(self, text: str, display_text: str) -> dict:
        university = self._detect_university(text)
        course = self._extract_course(display_text, university)

        return {
            "course": course,
            "university": university,
        }

    def _detect_university(self, text: str) -> str:
        for university in UNIVERSITY_ALIASES:
            if re.search(rf"\b{re.escape(university)}\b", text):
                return university

        return ""

    def _extract_course(self, display_text: str, university: str = "") -> str:
        patterns = [
            r"\bquero\s+fazer\s+(.+)$",
            r"\bmeu\s+curso\s+alvo\s+(?:e|eh|é)\s+(.+)$",
            r"\bquero\s+passar\s+em\s+(.+)$",
        ]

        course = ""

        for pattern in patterns:
            match = re.search(pattern, display_text)
            if match:
                course = match.group(1).strip()
                break

        if not course:
            return ""

        if university:
            course = re.sub(rf"\b(na|no|em)\s+{re.escape(university)}\b", " ", course)

        course = re.sub(r"\s+", " ", course).strip(" .?!,;:-")
        return course

    def _is_enem_strategy_question(self, text: str) -> bool:
        phrases = [
            "como eu melhoro minha nota no enem",
            "qual minha estrategia para o enem",
            "qual a minha estrategia para o enem",
            "como eu chego na minha meta",
            "o que eu preciso estudar para subir minha nota",
        ]
        return any(phrase in text for phrase in phrases)

    def _build_enem_strategy_response(self) -> str:
        score = self._to_int(self.academic_context.get("enem_score"))
        target = self._to_int(self.academic_context.get("enem_target"))
        priorities = self._enem_priorities()

        if score is not None and target is not None:
            gap = max(0, target - score)
            response = (
                f"Sua pontuação registrada é {score} e sua meta é {target}. "
                f"Você precisa evoluir cerca de {gap} pontos."
            )

            if priorities:
                return f"{response} {self._format_priority_response(priorities)}"

            return (
                f"{response} O próximo passo é identificar suas notas por área e "
                "priorizar as matérias com maior potencial de ganho."
            )

        if priorities:
            return self._format_priority_response(priorities)

        return (
            "Para montar uma estratégia precisa, preciso que você me informe sua nota geral, "
            "sua meta e, se possível, suas notas por área."
        )

    def _enem_priorities(self) -> list[str]:
        area_scores = self.academic_context.get("area_scores", {})
        priorities = []

        matematica = self._to_int(area_scores.get("matematica"))
        redacao = self._to_int(area_scores.get("redacao"))
        natureza = self._to_int(area_scores.get("natureza"))
        linguagens = self._to_int(area_scores.get("linguagens"))
        humanas = self._to_int(area_scores.get("humanas"))

        if matematica is not None and matematica < 700:
            priorities.append("matemática")

        if redacao is not None and redacao < 900:
            priorities.append("redação")

        if natureza is not None and natureza < 650:
            priorities.append("natureza")

        if linguagens is not None and linguagens < 650:
            priorities.append("linguagens")

        if humanas is not None and humanas < 650:
            priorities.append("humanas")

        return priorities

    def _format_priority_response(self, priorities: list[str]) -> str:
        priority_text = self._join_items(priorities)
        details = []

        if "matemática" in priorities:
            details.append("Matemática tende a ter alto impacto na nota")

        if "redação" in priorities:
            details.append("redação pode subir rápido com treino estruturado")

        if "natureza" in priorities:
            details.append("natureza exige revisão de base com questões")

        if "linguagens" in priorities or "humanas" in priorities:
            details.append("linguagens e humanas pedem leitura, interpretação e questões")

        return f"Com base nas suas informações, eu priorizaria: {priority_text}. {', '.join(details)}."

    def _join_items(self, items: list[str]) -> str:
        if len(items) <= 1:
            return "".join(items)

        return f"{', '.join(items[:-1])} e {items[-1]}"

    def _to_int(self, value: str | int | None) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _format_course_name(self, course: str) -> str:
        small_words = {"de", "da", "do", "das", "dos", "e", "em"}
        words = []

        for index, word in enumerate((course or "").split()):
            if index > 0 and word in small_words:
                words.append(word)
            else:
                words.append(word.capitalize())

        return " ".join(words)

    def _extract_study_target(self, text: str) -> str:
        patterns = [
            r"\bhoje\s+vamos\s+estudar\s+(.+)$",
            r"\bvamos\s+estudar\s+(.+)$",
            r"\bquero\s+estudar\s+(.+)$",
            r"\bbora\s+estudar\s+(.+)$",
            r"^estudar\s+(.+)$",
        ]
        return self._extract_with_patterns(text, patterns)

    def _extract_study_target_display(self, text: str) -> str:
        patterns = [
            r"\bhoje\s+vamos\s+estudar\s+(.+)$",
            r"\bvamos\s+estudar\s+(.+)$",
            r"\bquero\s+estudar\s+(.+)$",
            r"\bbora\s+estudar\s+(.+)$",
            r"^estudar\s+(.+)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._clean_display_extracted(match.group(1))

        return ""

    def _extract_difficulty(self, text: str) -> str:
        patterns = [
            r"\bminha\s+dificuldade\s+(?:e|eh|esta\s+em|ta\s+em)\s+(.+)$",
            r"\btenho\s+dificuldade\s+(?:em|com|de)\s+(.+)$",
            r"\bnao\s+entendi\s+(.+)$",
            r"\bestou\s+ruim\s+(?:em|com)\s+(.+)$",
        ]
        return self._extract_with_patterns(text, patterns)

    def _extract_learning(self, text: str) -> str:
        patterns = [
            r"\baprendi\s+hoje\s+sobre\s+(.+)$",
            r"\baprendi\s+sobre\s+(.+)$",
            r"\bentendi\s+melhor\s+(.+)$",
            r"\bagora\s+entendi\s+(.+)$",
            r"\baprendi\s+(.+)$",
        ]
        return self._extract_with_patterns(text, patterns)

    def _extract_with_patterns(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._clean_extracted(match.group(1))

        return ""

    def _detect_subject(self, text: str) -> str:
        for subject, aliases in SUBJECT_KEYWORDS.items():
            for alias in aliases:
                normalized_alias = normalize_text(alias)
                if re.search(rf"\b{re.escape(normalized_alias)}\b", text):
                    return subject

        return ""

    def _extract_topic(self, text: str, subject: str) -> str:
        topic = text

        if subject:
            for alias in SUBJECT_KEYWORDS.get(subject, []):
                normalized_alias = normalize_text(alias)
                topic = re.sub(rf"\b{re.escape(normalized_alias)}\b", " ", topic, count=1)

        return self._clean_extracted(topic)

    def _extract_topic_display(self, text: str, subject: str) -> str:
        topic = text

        if subject:
            for alias in SUBJECT_KEYWORDS.get(subject, []):
                topic = re.sub(rf"\b{re.escape(alias.lower())}\b", " ", topic, count=1)

        return self._clean_display_extracted(topic)

    def _is_current_context_question(self, text: str) -> bool:
        phrases = [
            "o que eu estou estudando",
            "o que eu estava estudando",
            "o que estou estudando",
            "o que estava estudando",
            "qual e meu foco agora",
            "qual meu foco agora",
            "onde parei",
            "qual o estudo atual",
        ]
        return any(phrase in text for phrase in phrases)

    def _is_next_step_question(self, text: str) -> bool:
        phrases = [
            "o que eu estudo agora",
            "qual o proximo passo",
            "o que eu faco agora",
            "como continuo",
        ]
        return any(phrase in text for phrase in phrases)

    def _is_explain_current_context_request(self, text: str) -> bool:
        phrases = [
            "voce nao vai me explicar",
            "explica melhor",
            "me explica melhor",
            "me explica de outro jeito",
            "nao entendi",
            "como assim",
            "nao ficou claro",
            "me ajuda a entender",
        ]
        return any(phrase in text for phrase in phrases)

    def _is_end_study_session(self, text: str) -> bool:
        phrases = [
            "terminei de estudar",
            "encerrar estudo",
            "parar estudo",
            "finalizar estudo",
        ]
        return any(phrase in text for phrase in phrases)

    def _explain_current_context(self) -> str:
        topic = self.current_context.get("topic", "")
        difficulty = self.current_context.get("difficulty", "")
        normalized_topic = normalize_text(topic)

        if "funcao do segundo grau" in normalized_topic or "segundo grau" in normalized_topic:
            explanation = (
                "Claro. Vou explicar de um jeito mais simples. Em uma função do segundo grau, "
                "o gráfico é uma parábola. O ponto mais importante é o vértice, porque ele mostra "
                "onde a curva muda de direção. As raízes mostram onde a parábola cruza o eixo x, "
                "e o valor de a indica se ela abre para cima ou para baixo."
            )

            if difficulty and "grafico" in normalize_text(difficulty):
                explanation += (
                    " Como sua dificuldade é interpretar gráfico, foque em identificar o vértice, "
                    "as raízes e a direção da concavidade antes de fazer contas."
                )

            return explanation

        if topic:
            explanation = (
                f"Claro. Vou explicar de um jeito mais simples. O tema atual é {topic}. "
                "Comece entendendo a ideia principal, depois veja um exemplo resolvido e, por fim, "
                "tente explicar com suas próprias palavras."
            )

            if difficulty:
                explanation += f" Como sua dificuldade atual é {difficulty}, vamos usar isso como ponto de revisão."

            return explanation

        return "Claro. Me diga qual tema você quer revisar e eu explico de um jeito mais simples."

    def _clean_extracted(self, text: str) -> str:
        text = normalize_text(text).strip(" .?!,;:-")
        text = re.sub(r"\s+", " ", text)

        while True:
            cleaned = re.sub(r"^(sobre|em|de|do|da|o|a)\s+", "", text).strip()
            if cleaned == text:
                return text
            text = cleaned

    def _display_text(self, text: str) -> str:
        text = (text or "").lower().strip(" .?!,;:-")
        return re.sub(r"\s+", " ", text).strip()

    def _clean_display_extracted(self, text: str) -> str:
        text = self._display_text(text)

        while True:
            cleaned = re.sub(r"^(sobre|em|de|do|da|o|a)\s+", "", text).strip()
            if cleaned == text:
                return text
            text = cleaned

    def _format_focus(self, subject: str, topic: str) -> str:
        if subject and topic:
            return f"{subject}, {topic}"

        return topic or subject

    def _storage_focus(self, subject: str, topic: str) -> str:
        if subject and topic:
            return f"{subject} - {topic}"

        return topic or subject

    def _split_focus_value(self, value: str) -> tuple[str, str]:
        value = (value or "").strip()

        if " - " in value:
            subject, topic = value.split(" - ", 1)
            return subject.strip(), topic.strip()

        return "", value

    def _decode_metadata(self, metadata: str | dict | None) -> dict:
        if isinstance(metadata, dict):
            return metadata

        if not metadata:
            return {}

        try:
            decoded = json.loads(metadata)
        except (TypeError, ValueError):
            return {}

        return decoded if isinstance(decoded, dict) else {}

    def _metadata(self, data: dict) -> dict:
        return {
            **data,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def _safe_save(self, method_name: str, *args, **kwargs):
        if self.memory_store is None:
            return

        try:
            func = getattr(self.memory_store, method_name)
            func(*args, **kwargs)
        except Exception as exc:
            print("Erro ao salvar contexto de estudo:", repr(exc))
