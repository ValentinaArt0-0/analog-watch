# Reloj Analógico en Python puro

Reloj analógico con interfaz gráfica escrito **100% en Python**, sin tkinter, sin librerías externas y con **un único import** (`ctypes`).

## Cómo ejecutarlo

1. Descarga `analog_clock.py`.
2. Abre una terminal en la carpeta del archivo.
3. Ejecuta:

```bash
python analog_clock.py
```

Al ejecutarlo se abre una ventana centrada en la pantalla con el reloj en funcionamiento. Se cierra con el botón de cerrar de la ventana.

## Qué muestra

- Cara del reloj con diseño oscuro, borde violeta y efecto de brillo exterior.
- 60 marcas (las de cada hora en cian y más gruesas) y los números del 1 al 12.
- Manecilla de la hora, del minuto y segundero (rosa, con cola y movimiento suave).
- Hora digital (`HH:MM:SS`) y fecha en español debajo del reloj.

## Cómo funciona

El archivo está organizado en capas, de arriba hacia abajo:

### 1. Configuración
Constantes al inicio: tamaño de la ventana (`WIDTH`, `HEIGHT`), centro y radio del reloj, colores y nombres de días y meses.

### 2. Matemáticas propias
- `sin(x)`: reduce el ángulo al rango `[-π, π]` y suma 11 términos de la serie de Taylor. El error máximo es de unos `1e-11`, imperceptible en pantalla.
- `cos(x)`: se obtiene como `sin(x + π/2)`.
- `point_on_circle(angulo, largo)`: devuelve la coordenada de un punto a cierta distancia del centro. Usa **0° = arriba** y avanza en sentido horario, igual que un reloj.
- `rgb("#rrggbb")`: convierte un color hexadecimal al formato `COLORREF` de Windows (`0x00BBGGRR`).

### 3. Capa de la API de Windows
- Se cargan `user32`, `gdi32` y `kernel32` con `ctypes.WinDLL`.
- Se definen las estructuras que Windows espera (`RECT`, `MSG`, `PAINTSTRUCT`, `SYSTEMTIME`, `WNDCLASS`).
- `bind(...)` declara los tipos de argumentos y de retorno de cada función, necesario para que funcione correctamente en Windows de 64 bits.

### 4. Funciones de dibujo
`draw_line`, `draw_circle`, `draw_text` y `draw_hand` envuelven las llamadas de GDI. Los lápices, pinceles y fuentes se guardan en cachés (`pens`, `brushes`, `fonts`) para crearlos una sola vez y no en cada fotograma.

### 5. Renderizado del reloj
- `draw_clock_face`: dibuja el fondo, los anillos de brillo, el borde, las marcas y los números.
- `draw_clock_hands`: lee la hora con `GetLocalTime` y calcula los ángulos:
  - `segundos = segundo + milisegundos / 1000` (segundero suave)
  - `minutos = minuto + segundos / 60`
  - `horas = (hora % 12) + minutos / 60`

  Cada valor se multiplica por los grados que recorre su manecilla (30° por hora, 6° por minuto y por segundo).
- `paint`: usa **doble búfer**; dibuja todo en un bitmap fuera de pantalla y lo copia a la ventana de una sola vez con `BitBlt`, evitando el parpadeo.

### 6. Ventana y bucle principal
- `window_proc` es la función que Windows llama con cada evento:
  - `WM_PAINT`: dibuja el reloj.
  - `WM_TIMER`: pide repintar la ventana.
  - `WM_DESTROY`: termina el programa.
- `main()` registra la clase de ventana, la crea con el área interior exacta de 460×520, la centra, inicia un temporizador de **16 ms** (unos 60 cuadros por segundo) y entra en el bucle de mensajes (`GetMessageW` → `DispatchMessageW`).

## Personalización

Todo se cambia en la sección de configuración al inicio del archivo:

| Qué cambiar | Constante |
|---|---|
| Tamaño de la ventana | `WIDTH`, `HEIGHT`, `CENTER_X`, `CENTER_Y` |
| Tamaño del reloj | `RADIUS` |
| Colores | `BACKGROUND`, `FACE`, `BORDER`, `NEON`, `HOUR_COLOR`, `MINUTE_COLOR`, `SECOND_COLOR`, `TEXT_COLOR` |
| Idioma de la fecha | `DAYS`, `MONTHS` |
| Fluidez | el valor `16` (milisegundos) en `user32.SetTimer(...)` dentro de `main()` |

## Limitaciones

- Solo funciona en Windows.
- GDI no tiene suavizado de bordes en las líneas, por lo que las manecillas se ven algo menos suaves que en tkinter.
- La ventana no es redimensionable (igual que el original).

## Estructura del proyecto

```
.
├── analog_clock.py   # todo el programa
└── README.md
```
