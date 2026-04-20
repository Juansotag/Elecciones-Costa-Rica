# Nowcasting Electoral con Machine Learning y Redes Sociales

## Descripción general
Este proyecto implementa un **pipeline completo de nowcasting electoral** basado en señales digitales de redes sociales y modelos de *Machine Learning*, aplicado al caso de la **segunda vuelta presidencial en Bolivia (2025)**. El objetivo es evaluar si, bajo **condiciones extremas de escasez de datos, ventanas temporales cortas y uso de herramientas comerciales**, es posible estimar con precisión la intención de voto en tiempo casi real.

El trabajo se inspira y extiende el marco **SoMEN (Social Media framework for Election Nowcasting)** de Brito & Adeodato, integrando múltiples redes sociales (Facebook, X/Twitter, Instagram y TikTok) y comparando modelos lineales y no lineales (MLP y GRNN).

---

## Pregunta de investigación
> ¿Cómo se comporta la capacidad predictiva de los modelos de Machine Learning aplicados a elecciones presidenciales en Latinoamérica cuando se adaptan a contextos de series temporales cortas y limitaciones severas de información?

---

## Objetivos

### Objetivo general
Aplicar modelos de Machine Learning (GRNN y MLP) para predecir los resultados de la elección presidencial boliviana de 2025, bajo restricciones reales de acceso a datos de redes sociales.

### Objetivos específicos
- Diseñar y validar un pipeline de recolección de datos vía *web scraping* y APIs comerciales.
- Construir un dataset diario de interacción en redes sociales durante los 180 días previos a la elección.
- Entrenar y evaluar modelos GRNN y MLP para estimar la intención de voto en segunda vuelta.

---

## Alcance del proyecto
- **Caso de estudio:** Segunda vuelta presidencial en Bolivia (19 de octubre de 2025).
- **Candidatos:** Rodrigo Paz Pereira (PDC) y Jorge “Tuto” Quiroga (Alianza Libre).
- **Ventana temporal:** 180 días previos a la elección.
- **Frecuencia:** Datos diarios.
- **Restricciones:**
  - Número reducido de encuestas.
  - Series temporales cortas.
  - Uso exclusivo de herramientas comerciales (sin infraestructura Big Data institucional).

---

## Fuentes de datos

### Redes sociales
Datos recolectados desde cuentas oficiales de campaña mediante *scraping* y APIs:
- **Facebook**
- **X (Twitter)**
- **Instagram**
- **TikTok**

Se utilizaron servicios de **Apify** y la **Twitter API**, orquestados con **Make.com**, para capturas periódicas y consistentes.

### Encuestas y resultados electorales
- Encuestas de Ipsos Ciesmori, SPIE, Captura Consulting y Ciemcorp.
- Resultado electoral oficial del Tribunal Supremo Electoral de Bolivia.

Las encuestas se interpolan linealmente para construir la variable objetivo diaria de intención de voto.

---

## Variables y features

Para cada candidato y día se construye un vector de características con **29 variables**, incluyendo:

- Volumen de publicaciones.
- Likes, comentarios, compartidos, retuits, favoritos.
- Métricas normalizadas por publicación (engagement por post).
- Variables específicas por plataforma.

Las métricas se **estandarizan por red social (z-score)** para evitar sesgos de escala.

---

## Metodología

### 1. Recolección de datos
- Scraping diario de publicaciones e interacciones.
- Consolidación por candidato–día.
- Homogeneización temporal del muestreo.

### 2. Limpieza y estandarización
- Agregación diaria.
- Normalización por publicación.
- Estandarización intra-plataforma.
- Prevención explícita de fuga temporal.

### 3. Construcción de la variable objetivo
- Interpolación lineal entre encuestas.
- Inclusión del resultado electoral como último punto.
- Predicción de una sola serie (candidato líder) y complemento al 100%.

### 4. Modelamiento
Modelos evaluados:
- Regresión lineal (baseline).
- Regresión lineal + PCA.
- MLP (Multilayer Perceptron).
- MLP + PCA.
- GRNN (General Regression Neural Network).
- GRNN + PCA.

### 5. Evaluación
Evaluación puntual el **día de la elección** usando:
- MAE (Error Absoluto Medio).
- MAPE (Error Porcentual Absoluto Medio).
- RMSE (Raíz del Error Cuadrático Medio).

---

## Resultados principales

- Los **modelos lineales fallan** en capturar la relación entre actividad digital e intención de voto.
- **MLP con PCA** obtiene el mejor desempeño:
  - MAE ≈ 0.0279
  - Error 6–10 veces menor que los modelos lineales.
- GRNN muestra desempeño intermedio.
- Las métricas digitales por sí solas **no reflejan linealmente el resultado electoral**, pero contienen señal predictiva relevante cuando se modelan de forma no lineal.

---

## Hallazgos clave
- El engagement en redes refleja **ruido acumulado**, no necesariamente el cambio final de intención de voto.
- El giro electoral ocurrió en la última semana y no fue capturado por métricas agregadas simples.
- TikTok mostró dinámicas distintas al resto de redes.
- La combinación **PCA + MLP** logra capturar factores latentes comunes entre plataformas.

---

## Limitaciones
- Serie temporal muy corta.
- Cambios abruptos de momentum electoral.
- Posibles sesgos de audiencia por plataforma.
- Caso de estudio único (balotaje).

Los resultados deben interpretarse como **condicionados al contexto** y no como generalización universal.

---

## Proyección y trabajo futuro
- Extensión a elecciones legislativas y locales.
- Ventanas móviles combinadas (diarias + mensuales).
- Integración de señales offline (prensa, territorio, economía).
- Detección de manipulación, bots y calidad de interacción.

---

## Estructura del repositorio (sugerida)

```
├── data/
│   ├── raw/                # Datos crudos de scraping
│   ├── processed/          # Datos agregados y estandarizados
├── notebooks/
│   ├── nowcasting_bolivia.ipynb
├── src/
│   ├── scraping/
│   ├── preprocessing/
│   ├── modeling/
│   └── evaluation/
├── docs/
│   └── metodologia.pdf
├── README.md
```

---

## Tecnologías utilizadas
- Python
- pandas, numpy, scikit-learn
- APIs comerciales (Apify, Twitter API)
- Make.com (orquestación)

---

## Consideraciones éticas
- Uso exclusivo de publicaciones públicas.
- No se recolecta información personal sensible.
- Enfoque académico y analítico.
- Resultados interpretados con cautela para evitar uso indebido.

---

## Referencias
El marco teórico y metodológico se basa principalmente en:
- Brito & Adeodato (2022, 2023)
- Lewis-Beck & Tien (2014)
- Skoric et al. (2020)

Ver documento completo del proyecto para referencias detalladas.

---

## Autor
**Juan Sotelo Aguilar**  
Proyecto académico – Machine Learning y Ciencia Política  
2025

