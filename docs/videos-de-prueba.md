# 🎬 Prompts para generar videos de prueba con IA — OMNI Agro

Prompts listos para Sora / Veo / Kling / Runway / Pika. Cada uno está diseñado
para que **los detectores del MVP funcionen** sobre el video generado.

## ⚠️ Reglas de oro (aplican a TODOS los prompts)

1. **Cámara CENITAL** (dron mirando 90° hacia abajo, "top-down / bird's eye").
   Las tomas oblicuas al horizonte NO sirven para contar plantas.
2. **Altura constante** equivalente a 10–30 m: cada planta debe verse como una
   "mota" verde de 30–120 px, separada de sus vecinas.
3. **Vuelo lento y recto** (avance tipo survey/mapeo), sin zoom, sin giros
   bruscos — ByteTrack pierde los IDs si la escena salta.
4. **Un solo plano continuo** de 8–10 segundos.
5. **Luz de día pareja** (mediodía nublado ideal), sin sombras largas.
6. Estilo **realista** (photorealistic), NO render 3D estilizado.
7. Para probar **despoblamiento**: pide explícitamente huecos en las hileras.
8. Para probar **malezas**: pide manchas de vegetación irregular entre surcos.

---

## 01 · CONTEO (huerto en hileras, estilo arándano/cítrico)

**Prompt EN:**
> Top-down aerial drone footage, camera pointing straight down at 90 degrees,
> flying slowly and steadily forward over an orchard with neat rows of round
> green bushes (blueberry farm style), each bush clearly separated by bare
> brown soil. Constant altitude of 20 meters, even midday light,
> photorealistic, single continuous 10 second shot, no camera rotation.

**Prompt ES:**
> Video aéreo de dron cenital, cámara apuntando 90° hacia abajo, avanzando
> lento y estable sobre un huerto con hileras ordenadas de arbustos verdes
> redondos (estilo fundo de arándanos), cada arbusto separado por suelo
> marrón. Altura constante de 20 m, luz de mediodía pareja, fotorrealista,
> plano único continuo de 10 s, sin rotación de cámara.

---

## 02 · DESPOBLAMIENTO (hileras con huecos)

**Prompt EN:**
> Top-down drone survey footage at constant 20 meter altitude over rows of
> green crop bushes on brown soil. Several plants are MISSING, leaving obvious
> empty gaps of bare soil inside otherwise complete rows. Slow steady forward
> flight, camera pointing straight down, even daylight, photorealistic,
> continuous 10 second shot.

**Prompt ES:**
> Video de dron cenital a 20 m constantes sobre hileras de arbustos verdes en
> suelo marrón. FALTAN varias plantas, dejando huecos evidentes de tierra
> desnuda dentro de hileras completas. Vuelo lento y recto, cámara 90° hacia
> abajo, luz pareja, fotorrealista, plano continuo de 10 s.

**Para la demo:** módulo 03 — las celdas de los huecos se pintan rojas y el
KPI de despoblamiento sube.

---

## 03 · MALEZAS (cultivo en surcos + manchas de maleza)

**Prompt EN:**
> Top-down drone footage at 15 meter constant altitude over young crop rows
> (small green seedlings in straight lines on dark soil). Irregular patches of
> wild weeds grow scattered BETWEEN the rows, clearly messier and a different
> shade of green than the crop. Slow forward survey flight, camera straight
> down, photorealistic, continuous 10 second shot.

**Prompt ES:**
> Video de dron cenital a 15 m constantes sobre surcos de cultivo joven
> (plántulas verdes en líneas rectas sobre suelo oscuro). Manchas irregulares
> de maleza silvestre crecen dispersas ENTRE los surcos, claramente más
> desordenadas y de otro tono de verde. Vuelo de mapeo lento, cámara 90° hacia
> abajo, fotorrealista, plano continuo de 10 s.

**Para la demo:** módulo 02 con modo "según modelo" — la presión de maleza
sube y dispara la alerta al pasar el umbral.

---

## 04 · ROI DE LOTE (dos lotes distintos en un frame)

**Prompt EN:**
> Top-down drone footage at 25 meter altitude showing two adjacent farm plots
> divided by a dirt road: left plot has dense healthy rows of green bushes,
> right plot has sparse rows with many missing plants. Camera pointing straight
> down, slow steady flight along the road, photorealistic, 10 seconds.

**Prompt ES:**
> Video de dron cenital a 25 m mostrando dos lotes agrícolas contiguos
> divididos por un camino de tierra: el lote izquierdo con hileras densas y
> sanas, el derecho con hileras ralas y muchas plantas faltantes. Cámara 90°
> hacia abajo, vuelo lento sobre el camino, fotorrealista, 10 s.

**Para la demo:** dibuja un ROI sobre cada lote por separado y compara el
despoblamiento entre ambos sobrevuelos.
