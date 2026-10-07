import cv2
import numpy as np
from PIL import Image
import time
import os
from concurrent.futures import ProcessPoolExecutor
from moviepy import VideoFileClip

# =========================================================
# FUNCIÓN INDEPENDIENTE (Obligatorio para multiprocesamiento)
# =========================================================
def convertir_a_blanco_y_negro(frame):
    # Requisito 1 y 2: Uso de OpenCV y Pillow para convertir los fotogramas a b/n
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    imagen_pil = Image.fromarray(frame_rgb)
    imagen_gris_pil = imagen_pil.convert('L')
    return np.array(imagen_gris_pil)

def procesar_video_final_sin_rtx(ruta_entrada, ruta_salida):
    # Requisito 3: Medición del tiempo total
    inicio_tiempo = time.time()
    archivo_temporal = "temp_multihilo.mp4"

    cap = cv2.VideoCapture(ruta_entrada)
    if not cap.isOpened():
        print(f"Error: No se pudo abrir '{ruta_entrada}'.")
        return

    # Requisito 4: Extraer y mantener la resolución 4K y los 60 fps
    ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(archivo_temporal, fourcc, fps, (ancho, alto), isColor=False)

    # Usa automáticamente TODOS los hilos de tu procesador i5
    hilos_disponibles = os.cpu_count()
    
    print("--- FASE 1: Procesamiento Paralelo con Pillow (CPU) ---")
    print(f"Detectados {hilos_disponibles} hilos en el procesador.")

    frames_procesados = 0
    lote_frames = []

    # Procesa los fotogramas del video cuidando la memoria RAM
    with ProcessPoolExecutor(max_workers=hilos_disponibles) as executor:
        while True:
            ret, frame = cap.read()
            
            if ret:
                lote_frames.append(frame)
            
            if len(lote_frames) == hilos_disponibles or (not ret and len(lote_frames) > 0):
                resultados = list(executor.map(convertir_a_blanco_y_negro, lote_frames))
                
                for frame_gris in resultados:
                    out.write(frame_gris)
                    frames_procesados += 1
                
                lote_frames.clear()

                # Mostrar progreso y tiempo restante estimado (Fase 1)
                if frames_procesados % (hilos_disponibles * 5) == 0 or not ret:
                    porcentaje = (frames_procesados / total_frames) * 100
                    
                    tiempo_transcurrido = time.time() - inicio_tiempo
                    if tiempo_transcurrido > 0:
                        fps_procesamiento = frames_procesados / tiempo_transcurrido
                        segundos_restantes = (total_frames - frames_procesados) / fps_procesamiento
                        
                        minutos_rest = int(segundos_restantes // 60)
                        seg_rest = int(segundos_restantes % 60)
                        tiempo_restante_str = f"{minutos_rest}m {seg_rest}s"
                    else:
                        tiempo_restante_str = "Calculando..."
                        
                    print(f"Progreso: {frames_procesados}/{total_frames} frames ({porcentaje:.1f}%) - Faltan aprox: {tiempo_restante_str}")

            if not ret:
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # ==========================================
    # FASE 2: AGREGAR AUDIO Y COMPRIMIR CON CPU
    # ==========================================
    print("\n--- FASE 2: Comprimiendo video con el procesador (libx264) ---")
    print("Advertencia: La compresión 4K por CPU tomará bastante tiempo...")
    try:
        video_original = VideoFileClip(ruta_entrada)
        video_procesado = VideoFileClip(archivo_temporal)

        try:
            video_final = video_procesado.with_audio(video_original.audio)
        except AttributeError:
            video_final = video_procesado.set_audio(video_original.audio)

        # Exportación usando el procesador con barra de progreso activa
        video_final.write_videofile(
            ruta_salida, 
            codec="libx264",
            audio_codec="aac",
            fps=fps,
            preset="ultrafast",
            bitrate="50000k",
            logger="bar"           # <--- MUESTRA LA BARRA DE CARGA Y EL TIEMPO RESTANTE
        )
        
        video_original.close()
        video_procesado.close()
        video_final.close()

        if os.path.exists(archivo_temporal):
            os.remove(archivo_temporal)

    except Exception as e:
        print(f"Ocurrió un error en la Fase 2: {e}")

    # ==========================================
    # RESULTADOS FINALES
    # ==========================================
    tiempo_total = time.time() - inicio_tiempo
    print(f"\n¡Proceso completado exitosamente sin usar la tarjeta gráfica!")
    print(f"Archivo final guardado en: {ruta_salida}")
    print(f"Tiempo total de la tarea realizada: {tiempo_total:.2f} segundos ({tiempo_total/60:.2f} minutos)")

if __name__ == "__main__":
    video_entrada = "Stunning 4K HDR 60fps Dolby VisionTM _ 4K Video Ultra HD(4K_60FPS).webm"
    video_salida = "salida_4k_solo_cpu.mp4"
    
    procesar_video_final_sin_rtx(video_entrada, video_salida)