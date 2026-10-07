import cv2
import numpy as np
from PIL import Image
import time
import os

# Importación corregida para las versiones más recientes de MoviePy
from moviepy import VideoFileClip

def procesar_4k_con_audio_corregido(ruta_entrada, ruta_salida):
    inicio_tiempo = time.time()
    archivo_temporal = "temp_silencioso.mp4"

    # ==========================================
    # FASE 1: PROCESAMIENTO DE IMAGEN (OPENCV + PILLOW)
    # ==========================================
    cap = cv2.VideoCapture(ruta_entrada)

    if not cap.isOpened():
        print(f"Error: No se pudo abrir el archivo '{ruta_entrada}'. Verifica que el nombre sea correcto.")
        return

    # Extraer propiedades del video original
    ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Escritor del archivo temporal (Solo video en blanco y negro)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(archivo_temporal, fourcc, fps, (ancho, alto), isColor=False)

    print("--- FASE 1: Procesando frames en 4K Blanco y Negro ---")
    print(f"Resolución: {ancho}x{alto} a {fps} FPS")
    
    frames_procesados = 0

    # Bucle de conversión de frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # OpenCV (BGR) -> Pillow (RGB) -> Blanco y Negro (L) -> OpenCV (Gris)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        imagen_pil = Image.fromarray(frame_rgb)
        imagen_gris_pil = imagen_pil.convert('L')
        frame_gris_cv2 = np.array(imagen_gris_pil)

        out.write(frame_gris_cv2)
        frames_procesados += 1

        # Mostrar progreso cada 60 frames (1 segundo aprox.)
        if frames_procesados % 60 == 0:
            porcentaje = (frames_procesados / total_frames) * 100
            print(f"Progreso: {frames_procesados}/{total_frames} frames ({porcentaje:.1f}%)")

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # ==========================================
    # FASE 2: AGREGAR AUDIO Y OPTIMIZAR (MOVIEPY)
    # ==========================================
    print("\n--- FASE 2: Añadiendo audio y optimizando formato final ---")
    print("Por favor espera, comprimir 4K puede tomar un momento...")

    try:
        # Cargar los videos con MoviePy
        video_original = VideoFileClip(ruta_entrada)
        video_procesado = VideoFileClip(archivo_temporal)

        # En MoviePy v2.x, para asignar audio usamos .with_audio() en lugar de .set_audio()
        try:
            video_final = video_procesado.with_audio(video_original.audio)
        except AttributeError:
            video_final = video_procesado.set_audio(video_original.audio)

        # Exportar con códec H.264 para evitar tirones
        video_final.write_videofile(
            ruta_salida, 
            codec="libx264", 
            audio_codec="aac",
            fps=fps,
            preset="ultrafast",
            logger=None
        )
        
        # Cerrar los archivos para liberar recursos
        video_original.close()
        video_procesado.close()
        video_final.close()

        # Limpiar el archivo temporal
        if os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)

    except Exception as e:
        print(f"Ocurrió un error en la Fase 2: {e}")

    # ==========================================
    # RESULTADOS
    # ==========================================
    tiempo_total = time.time() - inicio_tiempo
    print(f"\n¡Proceso completado exitosamente!")
    print(f"Archivo final guardado en: {ruta_salida}")
    print(f"Tiempo total de ejecución: {tiempo_total:.2f} segundos ({tiempo_total/60:.2f} minutos)")

if __name__ == "__main__":
    # Nombres exactos de los archivos
    video_entrada = "Stunning 4K HDR 60fps Dolby VisionTM _ 4K Video Ultra HD(4K_60FPS).webm"
    video_salida = "salida_4k_bn_con_audio.mp4"
    
    procesar_4k_con_audio_corregido(video_entrada, video_salida)