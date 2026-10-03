# Datasets y métricas para evaluar LLMs

Apuntes de referencia para elegir con qué y cómo evaluar un modelo. La parte práctica (BLEU y ROUGE en código) está en [`05_evaluation/metrics`](../05_evaluation/metrics).

## Algunos datasets (en español o multilingües)

| Dataset | Tarea | Qué evalúa |
|---|---|---|
| **Belebele** | QA / opción múltiple | Comprensión lectora: extraer información de un texto largo. |
| **COPA_es** | Clasificación | Razonamiento causal: elegir qué pasa después según la lógica del mundo real. |
| **fake_news_corpus_spanish** | Clasificación binaria | Decidir si una noticia es verdadera o falsa. |
| **ClinDiagnosES** | QA | Diagnóstico a partir de un caso clínico. |
| **ClinTreatES** | QA / generación | Diagnóstico y propuesta de tratamiento a partir de un caso clínico. |
| **multilingual-crows-pairs** | Pares de frases | Sesgos y estereotipos (raciales, de género, de clase...). |
| **EsCoLA** (`nbel/EsCoLA`) | Aceptabilidad | Si una frase es gramaticalmente aceptable. Es el dataset de los benchmarks de [`03_vllm`](../03_vllm). |

### Dos familias de razonamiento
- **Commonsense reasoning:** ¿tiene el modelo conocimiento básico del mundo? Mide la *anchura* (saber un poco de todo). Ejemplo: OpenBookQA.
- **Multi-hop reasoning:** ¿es capaz de encadenar varios pasos para llegar a una conclusión? Mide la *profundidad*. Ejemplo: HotpotQA.

## Métricas

### Respuesta cerrada (NLU, *Natural Language Understanding*)

**EM (Exact Match).** Vale 1 si la respuesta es idéntica a la referencia y 0 en otro caso. Se usa en opción múltiple.

| Respuesta correcta: «París» | EM |
|---|---|
| «París» | 1 |
| «La ciudad de París» | 0 |
| «Paris» (sin tilde) | 0 |

**F1.** Mide el solapamiento de palabras entre respuesta y referencia, así que premia acertar las palabras clave aunque la frase no sea idéntica.
- Referencia: «Hipertensión arterial sistémica».
- Respuesta: «El paciente tiene hipertensión arterial».
- Resultado: EM = 0, pero F1 ≈ 0,8, porque contiene «hipertensión arterial» aunque le falte «sistémica».

### Respuesta abierta (NLG, *Natural Language Generation*)

- **BLEU:** coincidencias exactas de n-gramas con la referencia, con penalización si la respuesta es demasiado corta. Pensada para traducción automática. «El paciente debe *tomar* la *medicación*...» frente a «...*beber* la *medicina*...» puntúa bajo-medio aunque el significado sea el mismo.
- **ROUGE:** cuánto de la referencia aparece en la respuesta (orientada al *recall*). Útil en resúmenes. «Es vital reposar, beber agua y tomar paracetamol» frente a «Debe tomar paracetamol y beber agua» puntúa alto aunque falte «reposar».
- **METEOR:** como BLEU, pero tiene en cuenta raíces y sinónimos. «El niño corrió hacia la casa» frente a «El pequeño corría hacia el hogar» puntúa alto.
- **BERTScore:** compara los *embeddings* de un modelo tipo BERT en lugar de las palabras. «La película fue un éxito total» frente a «El filme resultó ser un triunfo absoluto» puntúa casi 1.

> [!NOTE]
> Las métricas basadas en palabras (BLEU, ROUGE) dependen del idioma. Por ejemplo, el *stemmer* de `rouge_score` solo funciona en inglés; se ve en el notebook de [`05_evaluation/metrics`](../05_evaluation/metrics).

## Idea pendiente: evaluación de sesgos
Hicimos dos pruebas preliminares con **HateCheck-ES**: clasificar frases con `salamandra-7b-instruct` como juez, y usar un modelo de sentimiento como aproximación. Se quedaron en exploración porque no comparaban con las etiquetas del dataset ni calculaban ninguna métrica. Si alguien retoma el tema, un buen punto de partida es reutilizar el cliente asíncrono de [`03_vllm/05-structured-scaling`](../03_vllm/05-structured-scaling) y medir accuracy/F1 frente a las etiquetas de HateCheck.
