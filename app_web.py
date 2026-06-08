import streamlit as st
import mido
import json

# Configuración de la página web
st.set_page_config(page_title="Mi Flauta Digital - Aula de Música", page_icon="🎵", layout="centered")

# Estilos CSS: Colores invertidos (Fondo oscuro, texto claro)
st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E28;
        color: #FFFFFF;
    }
    h1, h2, h3, p, label {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎵 Simulador de Flauta Dulce Interactiva")
st.write("Sube tu archivo MIDI y usa los controles para ensayar.")

# =====================================================================
# MAPA DE DIGITACIÓN Y LÓGICA MIDI
# =====================================================================
DIGITACION = {
    60: [1, 1, 1, 1, 1, 1, 1, 1],  # Do
    62: [1, 1, 1, 1, 1, 1, 1, 0],  # Re
    64: [1, 1, 1, 1, 1, 1, 0, 0],  # Mi
    65: [1, 1, 1, 1, 1, 0, 0, 0],  # Fa
    67: [1, 1, 1, 1, 0, 0, 0, 0],  # Sol
    69: [1, 1, 1, 0, 0, 0, 0, 0],  # La
    71: [1, 1, 0, 0, 0, 0, 0, 0],  # Si
    72: [1, 0, 1, 0, 0, 0, 0, 0],  # Do agudo
    74: [0, 0, 1, 0, 0, 0, 0, 0],  # Re agudo
}

NOMBRES_NOTAS = {60:"Do", 62:"Re", 64:"Mi", 65:"Fa", 67:"Sol", 69:"La", 71:"Si", 72:"Do agudo", 74:"Re agudo"}

def midi_a_frecuencia(nota_midi):
    return 440.0 * (2.0 ** ((nota_midi - 69.0) / 12.0))

# Selectores de la interfaz
col1, col2 = st.columns(2)
with col1:
    velocidad = st.selectbox("🐢 Velocidad:", ["100% (Normal)", "75%", "50%", "25%"])
    dict_vel = {"100% (Normal)": 1.0, "75%": 0.75, "50%": 0.50, "25%": 0.25}
    factor_velocidad = dict_vel[velocidad]
with col2:
    audio_opcion = st.radio("🔊 Sonido:", ["Si", "Silencio"])
    mute_activado = "true" if audio_opcion == "Silencio" else "false"

archivo_subido = st.file_uploader("📥 Arrastra aquí tu MIDI", type=["mid", "midi"])

if archivo_subido is not None:
    try:
        mid = mido.MidiFile(file=archivo_subido)
        eventos_raw = []
        tiempo_acumulado = 0.0
        
        for msg in mid:
            tiempo_acumulado += msg.time
            if msg.type in ['note_on', 'note_off']:
                eventos_raw.append({'tiempo': tiempo_acumulado, 'type': msg.type, 'note': msg.note, 'velocity': msg.velocity})
        
        partitura_final = []
        for i, ev in enumerate(eventos_raw):
            if ev['type'] == 'note_on' and ev['velocity'] > 0:
                duracion = 0.2
                for sig in eventos_raw[i+1:]:
                    if sig['note'] == ev['note'] and (sig['type'] == 'note_off' or sig['velocity'] == 0):
                        duracion = sig['tiempo'] - ev['tiempo']
                        break
                if ev['note'] in DIGITACION:
                    partitura_final.append({
                        'tiempo_inicio': ev['tiempo'],
                        'duracion': duracion,
                        'frecuencia': midi_a_frecuencia(ev['note']),
                        'nombre': NOMBRES_NOTAS[ev['note']],
                        'agujeros': DIGITACION[ev['note']]
                    })
        
        partitura_json = json.dumps(partitura_final)

        # =====================================================================
        # PROGRAMACIÓN DEL COMPONENTE WEB (MÉTODO SEGURO SIN F-STRINGS)
        # =====================================================================
        plantilla_html = """
        <div style="background-color: #2D2D3D; padding: 25px; border-radius: 15px; border: 2px solid #FF6464; text-align: center; font-family: sans-serif;">
            
            <div style="display: flex; justify-content: center; gap: 15px; margin-bottom: 20px;">
                <button id="btn-play" style="background-color: #28A745; color: white; border: none; padding: 12px 25px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold; flex: 1;">▶️ PLAY</button>
                <button id="btn-pause" style="background-color: #FFC107; color: black; border: none; padding: 12px 25px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold; flex: 1;" disabled>⏸️ PAUSE</button>
                <button id="btn-stop" style="background-color: #DC3545; color: white; border: none; padding: 12px 25px; font-size: 18px; border-radius: 8px; cursor: pointer; font-weight: bold; flex: 1;" disabled>⏹️ STOP</button>
            </div>
            
            <div id="pantalla-nota" style="font-size: 36px; font-weight: bold; margin: 20px 0; color: #FFFFFF; min-height: 45px;">Nota: Silencio</div>
            
            <div style="display: flex; justify-content: center; align-items: flex-start; gap: 20px; margin-top: 15px; position: relative; padding-left: 80px; width: fit-content; margin-left: auto; margin-right: auto;">
                
                <div style="display: flex; flex-direction: column; align-items: center; position: absolute; left: 0px; top: 15px;">
                    <span style="color: white; font-weight: bold; font-size: 16px; margin-bottom: 5px;">Pulgar</span>
                    <div id="agujero-P" style="width: 26px; height: 26px; border-radius: 50%; background-color: #321E14; border: 2px solid white; box-shadow: 0 0 8px rgba(255,255,255,0.2);"></div>
                </div>

                <div style="width: 65px; background-color: #D2B48C; border-radius: 15px; padding: 20px 0; display: flex; flex-direction: column; align-items: center; gap: 20px; border: 4px solid #503214; z-index: 2;">
                    <div id="agujero-1" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                    <div id="agujero-2" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                    <div id="agujero-3" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                    <div id="agujero-4" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                    <div id="agujero-5" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                    <div id="agujero-6" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                    <div id="agujero-7" style="width: 28px; height: 28px; border-radius: 50%; background-color: #321E14; border: 2px solid #1E1E28;"></div>
                </div>

            </div>
        </div>

        <script>
        const partitura = __PARTITURA_JSON__;
        const factorVelocidad = __FACTOR__;
        const mute = __MUTE__;
        
        let audioCtx = null;
        let osciladoresActivos = [];
        let timeoutsActivos = [];
        
        let tiempoActualMusical = 0; 
        let momentoUltimoPlay = 0; 
        let estaReproduciendo = false;
        
        const btnPlay = document.getElementById('btn-play');
        const btnPause = document.getElementById('btn-pause');
        const btnStop = document.getElementById('btn-stop');
        const notaTxt = document.getElementById('pantalla-nota');
        const idsHoles = ['agujero-P', 'agujero-1', 'agujero-2', 'agujero-3', 'agujero-4', 'agujero-5', 'agujero-6', 'agujero-7'];
        
        function updateFlauta(holes) {
            const cOn = "#FF6464"; const cOff = "#321E14";
            idsHoles.forEach((id, i) => {
                const el = document.getElementById(id);
                if (el) { el.style.backgroundColor = (holes[i] === 1) ? cOn : cOff; }
            });
        }

        function stopTodo() {
            osciladoresActivos.forEach(o => { try { o.stop(); } catch(e) {} });
            osciladoresActivos = [];
            timeoutsActivos.forEach(clearTimeout);
            timeoutsActivos = [];
            notaTxt.innerText = "Nota: Silencio";
            updateFlauta([0,0,0,0,0,0,0,0]);
        }

        btnPlay.onclick = () => {
            if (!audioCtx) { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); }
            
            estaReproduciendo = true;
            btnPlay.disabled = true; btnPause.disabled = false; btnStop.disabled = false;
            momentoUltimoPlay = audioCtx.currentTime;
            
            const baseAudio = audioCtx.currentTime;

            partitura.forEach(n => {
                const start = n.tiempo_inicio / factorVelocidad;
                const dur = n.duracion / factorVelocidad;
                
                if (start + dur <= tiempoActualMusical) { return; }

                let delay = Math.max(0, start - tiempoActualMusical);
                let durAjustada = (start < tiempoActualMusical) ? (start + dur - tiempoActualMusical) : dur;

                // AUDIO
                if (!mute) {
                    let o1 = audioCtx.createOscillator(); let g1 = audioCtx.createGain();
                    let o2 = audioCtx.createOscillator(); let g2 = audioCtx.createGain();
                    o1.type = 'sine'; o1.frequency.setValueAtTime(n.frecuencia, baseAudio + delay);
                    o2.type = 'sine'; o2.frequency.setValueAtTime(n.frecuencia * 2, baseAudio + delay);
                    
                    g1.gain.setValueAtTime(0, baseAudio + delay);
                    g1.gain.linearRampToValueAtTime(0.2, baseAudio + delay + 0.02);
                    g1.gain.setValueAtTime(0.2, baseAudio + delay + durAjustada - 0.02);
                    g1.gain.linearRampToValueAtTime(0, baseAudio + delay + durAjustada);
                    
                    o1.connect(g1); g1.connect(audioCtx.destination);
                    o2.connect(g2); g2.connect(audioCtx.destination); g2.gain.value = 0.02;

                    o1.start(baseAudio + delay); o1.stop(baseAudio + delay + durAjustada);
                    o2.start(baseAudio + delay); o2.stop(baseAudio + delay + durAjustada);
                    osciladoresActivos.push(o1, o2);
                }

                // GRÁFICOS
                timeoutsActivos.push(setTimeout(() => {
                    notaTxt.innerText = "Nota: " + n.nombre;
                    updateFlauta(n.agujeros);
                }, delay * 1000));

                timeoutsActivos.push(setTimeout(() => {
                    if (notaTxt.innerText === "Nota: " + n.nombre) {
                        notaTxt.innerText = "Nota: Silencio";
                        updateFlauta([0,0,0,0,0,0,0,0]);
                    }
                }, (delay + durAjustada) * 1000));
            });
            
            const duracionTotal = partitura[partitura.length - 1].tiempo_inicio + partitura[partitura.length - 1].duracion;
            const delayFinal = Math.max(0, (duracionTotal / factorVelocidad) - tiempoActualMusical);
            timeoutsActivos.push(setTimeout(() => {
                if (estaReproduciendo) {
                    estaReproduciendo = false;
                    tiempoActualMusical = 0;
                    btnPlay.disabled = false; btnPause.disabled = true; btnStop.disabled = true;
                }
            }, delayFinal * 1000));
        };

        btnPause.onclick = () => {
            estaReproduciendo = false;
            btnPlay.disabled = false; btnPause.disabled = true;
            tiempoActualMusical += (audioCtx.currentTime - momentoUltimoPlay);
            stopTodo();
        };

        btnStop.onclick = () => {
            estaReproduciendo = false;
            tiempoActualMusical = 0;
            btnPlay.disabled = false; btnPause.disabled = true; btnStop.disabled = true;
            stopTodo();
        };
        </script>
        """
        
        # Reemplazos dinámicos seguros sin usar f-strings
        html_reproductor = plantilla_html.replace("__PARTITURA_JSON__", partitura_json)
        html_reproductor = html_reproductor.replace("__FACTOR__", str(factor_velocidad))
        html_reproductor = html_reproductor.replace("__MUTE__", mute_activado)
        
        st.components.v1.html(html_reproductor, height=550)
            
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("👋 Sube un archivo MIDI para empezar.")
