# WMA Golden Cross Alert System 📈

Sistema de alertas automatizado basado en el cruce de medias móviles ponderadas (WMA) para la detección de señales "Golden Cross" (Cruce Dorado). El sistema escanea diferentes mercados, genera gráficos detallados y envía notificaciones por correo electrónico.

## ✨ Características

- **Análisis Multi-mercado**: Soporte para S&P 500, NASDAQ 100, Dow Jones y listas personalizadas.
- **Detección Automática**: Identifica el cruce de la WMA corta (30) sobre la WMA larga (200).
- **Generación de Gráficos**: Crea gráficos visuales de los últimos 300 días para cada alerta detectada.
- **Notificaciones por Email**: Envía reportes HTML con los gráficos adjuntos.
- **Persistencia**: Registra los eventos detectados para evitar alertas duplicadas.
- **Modo Revalidación**: Permite re-escanear fechas pasadas para asegurar que no se perdió ninguna señal.

## 🚀 Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/tu-usuario/wma-cross-alerts.git
   cd wma-cross-alerts
   ```

2. **Crear un entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuración

1. **Variables de entorno**:
   Copia el archivo de ejemplo y rellena tus datos:
   ```bash
   cp .env.example .env
   ```
   Edita `.env` con tu API Key de Financial Modeling Prep (FMP) y tus credenciales SMTP (se recomienda usar "Contraseñas de aplicación" de Gmail).

2. **Archivo de configuración (`config/config.yaml`)**:
   Define los mercados y los periodos de las medias móviles en este archivo.

## 🛠️ Uso

Para ejecutar el sistema con la fecha actual:
```bash
python src/wma_cross_alerts/main.py
```

Para ejecutar una fecha específica:
```bash
python src/wma_cross_alerts/main.py --date 2026-03-24
```

Modo revalidación (para chequear días anteriores):
```bash
python src/wma_cross_alerts/main.py --mode revalidation --date 2026-03-23
```

## 📁 Estructura del Proyecto

- `src/`: Código fuente del sistema.
- `config/`: Archivos de configuración YAML.
- `data/`: Almacenamiento de universos de símbolos y eventos detectados (creado automáticamente).
- `logs/`: Registros de ejecución (creado automáticamente).
- `scripts/`: Scripts auxiliares de utilidad.
