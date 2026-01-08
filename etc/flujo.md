# Arquitectura y Flujo del Sistema  
## Proyecto: wma-cross-alerts

Este documento describe **cómo funciona el sistema de alertas**, cómo se conectan sus componentes y cuál es el **flujo diario de ejecución**.

El objetivo del sistema es **detectar señales técnicas confirmadas al cierre diario** (actualmente Golden Cross WMA 30/200), **registrarlas**, **verificarlas visualmente** y **notificarlas** por email, de forma fiable y auditable.

---

## Visión general

> Cada día, tras el cierre del mercado, el sistema descarga datos, calcula indicadores, comprueba si hay señales, las registra, genera una gráfica y notifica si procede.

Principios clave:
- Ejecución **una vez al día**
- Señales **confirmadas** (no intradía)
- Persistencia de datos y eventos
- Notificaciones **no duplicadas**
- Evidencia visual para cada alerta

---

## Flujo diario completo

### 0. Arranque
El sistema se ejecuta automáticamente (por ejemplo, mediante el Programador de tareas).

Punto de entrada:
- `src/wma_cross_alerts/main.py`

---

### 1. Carga de configuración
Archivos implicados:
- `config/config.yaml`
- `core/settings.py`

Aquí se define:
- Qué activos vigilar (SP500, Nasdaq, acciones, etc.)
- Qué señales están activas (Golden Cross WMA)
- Ventana temporal de la gráfica
- Canales de notificación

No hay lógica de negocio en esta fase, solo decisiones de configuración.

---

### 2. Obtención de datos diarios
Archivos implicados:
- `data_sources/yahoo.py`
- `data/raw/`

Para cada símbolo configurado:
- Se descargan datos diarios (1D, precio de cierre)
- Se guarda el histórico actualizado en `data/raw/`

Este paso ocurre **todos los días**, haya o no señal.

---

### 3. Cálculo de indicadores
Archivos implicados:
- `indicators/wma.py`
- `data/processed/`

Sobre los datos descargados:
- Se calcula WMA(30)
- Se calcula WMA(200)
- Se guarda el resultado procesado

En esta fase **solo hay matemáticas**, no decisiones.

---

### 4. Detección de señales
Archivos implicados:
- `signals/golden_cross_wma.py`

Para cada símbolo:
- Se comparan las dos últimas sesiones
- Condición del Golden Cross:
  - Día anterior: WMA30 ≤ WMA200
  - Día actual:   WMA30 > WMA200

Resultados posibles:
- No hay señal → se continúa
- Hay señal → se genera un evento

Detectar una señal **no implica notificarla**.

---

### 5. Registro del evento
Archivos implicados:
- `persistence/storage.py`
- `data/events/`

Cuando se detecta una señal:
- Se crea un fichero JSON con:
  - Fecha
  - Símbolo
  - Tipo de evento
  - Valores usados para la detección

Este registro existe aunque falle la notificación.

---

### 6. Control de duplicados
Archivos implicados:
- `persistence/state.py`

Antes de notificar:
- Se comprueba si el evento ya fue notificado
- Si ya existe, no se envía nada
- Si es nuevo, se continúa el flujo

Esto evita alertas repetidas.

---

### 7. Generación de gráfica
Archivos implicados:
- `reporting/plotter.py`
- `data/charts/`

Para eventos nuevos:
- Se genera una gráfica con:
  - Precio
  - WMA30
  - WMA200
  - Marca visual del cruce
- Se guarda como PNG

Esta gráfica sirve como evidencia visual y se adjunta al email.

---

### 8. Notificación
Archivos implicados:
- `notifiers/email.py`

Se envía un email con:
- Resumen de la señal
- Activo y fecha
- Gráfica adjunta

El canal de notificación está desacoplado del resto del sistema.

---

### 9. Cierre y logging
Archivos implicados:
- `logs/app.log`
- `data/events/`

Se registra:
- Que el evento fue notificado
- Resultado del envío
- Información de la ejecución diaria

El sistema finaliza hasta el siguiente día.

---

## Esquema simplificado del flujo

```
Programador diario
        ↓
      main.py
        ↓
  config/config.yaml
        ↓
   Yahoo Finance
        ↓
     data/raw
        ↓
   indicadores (WMA)
        ↓
   data/processed
        ↓
   detectar señales
        ↓
   data/events
        ↓
 ¿ya notificado?
    ↓        ↓
   NO       SÍ
    ↓        ↓
 generar      salir
  gráfica
    ↓
 enviar email
    ↓
   logs
```

---

## Conclusión

Este diseño permite:
- Trazabilidad completa de cada alerta
- Verificación visual de las señales
- Escalabilidad a nuevos mercados y señales
- Simplicidad sin perder fiabilidad
- Evolución futura hacia base de datos si fuera necesario

Este documento define el **flujo oficial del sistema** y sirve como referencia permanente del proyecto.