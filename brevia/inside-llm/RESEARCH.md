# Brevia · Investigación: actuar DENTRO de la ingeniería del LLM, no desde fuera

> Pregunta de Miguel (19 jun 2026): *"lo interesante sería que actúe dentro de la
> ingeniería del LLM, no desde fuera... quizás desde el aplicativo yo pueda crear
> una GPT para OpenAI, o un Gem para Google, o una Skill."*

Esta es la pregunta más importante del proyecto. Aquí va el análisis honesto.

---

## 1. Dos mundos: fuera vs dentro

| | **FUERA** (Brevia hoy) | **DENTRO** (la idea de Miguel) |
|---|---|---|
| Qué es | Pre-procesa el texto antes de que llegue al modelo (CLI, extensión) | Vive dentro de la plataforma (Custom GPT, Gem, Skill, API) |
| Ahorro real de tokens | **Sí** — corta texto antes de enviarlo | **Depende** (ver abajo) |
| Distribución | El usuario instala algo | Sin instalar — un link en la tienda |
| Model-agnostic | Sí | Atado a cada plataforma |

La clave es: **¿quién toca el texto primero?** El que toca el texto antes de
tokenizar es el que puede ahorrar tokens de entrada. Y ahí está toda la verdad.

---

## 2. Verdad incómoda sobre Custom GPT / Gem / Skill

Un Custom GPT (OpenAI), un Gem (Google) o una Skill/Project (Claude) son, en
esencia: **un system prompt guardado + (a veces) herramientas y conocimiento.**

Cuando un usuario les habla:

1. La plataforma recibe el texto del usuario **completo**.
2. Le **suma** las instrucciones del GPT/Gem/Skill (eso son *más* tokens, no menos).
3. Recién entonces el modelo lo lee.

**Conclusión dura:** una instrucción del tipo *"comprime el contexto / sé
eficiente"* **NO reduce los tokens de entrada que la plataforma factura**, porque
la instrucción no puede interceptar el texto del usuario *antes* de que la
plataforma lo tokenice. Llega tarde. (Confirmado: el system prompt se cuenta y se
cobra; ver fuentes.)

**Lo que SÍ logran (no es poco):**
- **Acortar la SALIDA del modelo** → los tokens de salida sí bajan (en API cuestan
  más que los de entrada; en plan de suscripción se traduce en respuestas más
  rápidas y conversaciones más largas antes del límite de contexto).
- **Cambiar el comportamiento** → enseñar al modelo a pedir *referencias* en vez
  de documentos re-pegados, a resumir el contexto corriente, a no repetir.
- **Distribución masiva** → cero instalación, llegan al usuario no técnico (tu
  objetivo). Esto es ENORME para adopción.

**Matiz de planes de consumidor** (ChatGPT Plus, Gemini Advanced, Claude Pro): el
usuario paga una suscripción fija, no por token. Para él "ahorrar tokens" significa
**caber más en el contexto, ir más rápido y chocar menos con los límites** — no un
contador de dólares. El contador de dólares real es para quien usa la **API**.

---

## 3. El verdadero "dentro de la ingeniería" (donde tu instinto acierta)

Hay UN lugar donde se puede ahorrar tokens de entrada de verdad y aún así estar
"dentro": **el proxy / gateway entre la app y la API del modelo.**

Es un patrón real y en crecimiento (mercado de middleware LLM creciendo ~49.6%
anual). Ejemplos vivos:
- **Kong** tiene un plugin de compresión de prompts que quita relleno y palabras
  redundantes *antes* de que el request llegue al proveedor.
- Hay **proxies open-source** que se sientan entre el agente y la API y comprimen
  el historial / quitan definiciones de tools redundantes antes de enviar.

Esto **sí** reduce los tokens facturados, **sí** es model-agnostic (un proxy puede
hablar con OpenAI, Anthropic y Google), y **sí** está "dentro de la ingeniería"
(es parte del pipeline, no un copy/paste del usuario).

```
App / Agente  ──>  [ BREVIA PROXY ]  ──>  OpenAI / Anthropic / Google
                    comprime aquí
                    (dedup, cápsulas, semántica)
                    y mide el ahorro real
```

Y para Claude específicamente, el equivalente nativo "dentro" es un **servidor MCP**:
Claude (Code o Desktop) llama herramientas de Brevia para comprimir contexto a
demanda. Eso es estar dentro de la ingeniería de Claude.

---

## 4. Arquitectura recomendada: las dos capas juntas

No es "fuera VS dentro" — es **fuera Y dentro**, cada uno en su rol:

1. **Puerta de entrada (dentro / distribución):** Claude Skill + Custom GPT + Gem.
   - Hacen la salida concisa, enseñan el uso de referencias, y pueden **llamar** al
     motor Brevia como herramienta cuando el usuario pide "comprime esto".
   - Sirven para llegar a la masa no técnica sin instalar nada.

2. **Capa de reducción real (el moat / lo defendible):**
   - **Proxy/middleware Brevia** para devs y API → ahorro de tokens facturados,
     model-agnostic. *La dirección comercial más seria.*
   - **Extensión de navegador** (ya hecha, B3) → única forma de tocar el texto
     antes de que la plataforma de consumidor lo vea.
   - **Servidor MCP** → "dentro" de Claude.

---

## 5. Nuevos hitos que esto añade al roadmap

- **B6 · Proxy/Gateway Brevia** — drop-in `base_url` que comprime antes de reenviar
  a OpenAI/Anthropic/Google. El ahorro de tokens real "dentro de la ingeniería".
  *Probable núcleo comercial.*
- **B7 · Paquetes de entrega** — Claude Skill + Custom GPT + Gem, como puerta de
  entrada y front-end del motor/proxy. (Prototipos de instrucciones ya creados en
  esta carpeta.)
- **B5 · Servidor MCP** (ya estaba) — encaja aquí como el "dentro" nativo de Claude.

---

## 6. Veredicto honesto para Miguel

Tu instinto es correcto: **lo de fuera (extensión) es el inicio, no el final.** El
futuro defendible está "dentro" — pero ojo dónde:
- Custom GPT / Gem / Skill = **distribución y comportamiento** (no ahorro de input).
  Hazlos igual: son el canal para llegar a la gente.
- Proxy / MCP = **ahorro real de tokens dentro del pipeline**. Ahí está el producto
  serio, model-agnostic, que mide dólares de verdad.

El plan: empezar la tormenta en Claude (Skill + MCP) porque es donde más control
"dentro" tenemos hoy, y en paralelo prototipar el proxy que es lo que escala a
cualquier LLM.

---

## Fuentes
- OpenAI API Pricing — https://openai.com/api/pricing/
- Cómo reviso mi uso de tokens (OpenAI) — https://help.openai.com/en/articles/6614209-how-do-i-check-my-token-usage
- LLM Token Optimization with Enterprise AI Gateways (Kong, etc.) — https://www.getmaxim.ai/articles/llm-token-optimization-with-top-enterprise-ai-gateways/
- Open-Source Proxy Cuts Agent LLM Token Overhead — https://aiweekly.co/alerts/open-source-proxy-cuts-agent-llm-token-overhead
- LLM Token Optimization (Redis) — https://redis.io/blog/llm-token-optimization-speed-up-apps/
- LLMLingua / LongLLMLingua (compresión hard) — https://arxiv.org/pdf/2312.03863
- 500xCompressor (compresión soft hasta 480x) — https://arxiv.org/pdf/2408.03094

*Nota: capacidades exactas de cada plataforma (Actions, Gems, Skills) pueden
cambiar; verificar al construir B7. La lógica arquitectónica se mantiene.*
