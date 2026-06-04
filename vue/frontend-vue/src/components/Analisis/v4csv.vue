<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma 
        titulo="Sincronización de Historial IoT"
        subtitulo="Gestión masiva de datos y enrutamiento inteligente"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="carga-masiva-wrapper">
        
        <!-- SELECTORES INTELIGENTES -->
        <div class="header-dashboard shadow-soft mb-4">
          <div class="header-titles">
            <h2 class="main-title">Enrutamiento de Datos</h2>
            <span class="sub-title text-muted-custom">Selecciona el destino de TU información</span>
          </div>
          
          <div class="header-selectors">
            <div class="input-compact">
              <i class="bi bi-folder2-open icon-purple"></i>
              <select v-model="proyectoId" @change="cambiarProyecto" class="select-invisible">
                <option :value="null" disabled>{{ loadingProyectos ? 'Cargando...' : 'Selecciona Proyecto' }}</option>
                <option v-for="p in proyectos" :key="p.id" :value="p.id">{{ p.nombre }}</option>
              </select>
            </div>
            <div class="input-compact">
              <i class="bi bi-cpu icon-purple"></i>
              <select v-model="dispositivoId" @change="cambiarDispositivo" class="select-invisible" :disabled="!proyectoId">
                <option :value="null" disabled>{{ loadingDispositivos ? 'Cargando...' : 'Selecciona Dispositivo' }}</option>
                <option v-for="d in dispositivos" :key="d.id" :value="d.id">{{ d.nombre }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="grid-configuracion">
          <!-- FUENTE DE DATOS -->
          <div class="tarjeta-interfaz shadow-soft">
            <h2 class="subtitulo-interfaz">
              <i class="bi bi-file-earmark-arrow-up-fill"></i> Fuente de Datos CSV
            </h2>
            
            <div 
              class="area-soltar" 
              :class="{ 'archivo-listo': file }"
              @click="$refs.fileInput.click()"
            >
              <input 
                type="file" 
                ref="fileInput" 
                @change="handleFileChange" 
                accept=".csv" 
                hidden
              >
              <div class="icono-soltar"><i class="bi bi-cloud-upload"></i></div>
              <span v-if="!file" class="texto-soltar">Haz clic para seleccionar el archivo CSV</span>
              <span v-else class="nombre-archivo">{{ file.name }}</span>
            </div>

            <div v-if="status.message" :class="['estado-alerta', status.type]">
              <i :class="status.type === 'success' ? 'bi bi-check-circle-fill' : 'bi bi-info-circle-fill'"></i>
              {{ status.message }}
            </div>
          </div>

          <!-- EJECUCIÓN -->
          <div class="tarjeta-interfaz seccion-ejecucion shadow-soft">
             <h2 class="subtitulo-interfaz">
              <i class="bi bi-rocket-takeoff-fill"></i> Sincronización
            </h2>
            
            <div class="ejecucion-body">
              <button 
                @click="startUpload" 
                :disabled="!file || !dispositivoId || uploading"
                class="btn-ejecutar"
              >
                <i v-if="!uploading" class="bi bi-play-circle-fill"></i>
                <span v-else class="spinner-carga"></span>
                {{ uploading ? 'Procesando Lotes...' : 'Iniciar Sincronización Masiva' }}
              </button>

              <div v-if="uploading || progress > 0" class="progreso-contenedor">
                <div class="meta-progreso">
                  <span>Sincronizando base de datos</span>
                  <span>{{ progress }}%</span>
                </div>
                <div class="barra-base">
                  <div class="barra-relleno" :style="{ width: progress + '%' }"></div>
                </div>
                
                <div class="tiempo-estimado mt-3 d-flex justify-content-between text-muted-custom small fw-bold">
                  <span><i class="bi bi-stopwatch"></i> Transcurrido: {{ tiempoTranscurridoFmt }}</span>
                  <span v-if="tiempoRestante > 0" class="text-primary"><i class="bi bi-clock-history"></i> Restante estimado: {{ tiempoRestanteFmt }}</span>
                  <span v-else class="text-primary"><i class="bi bi-clock-history"></i> Calculando tiempo...</span>
                </div>

                <div class="detalles-progreso">
                  <div class="metrica-item">
                    <span class="etiqueta">Procesados</span>
                    <span class="valor">{{ processedRows }}</span>
                  </div>
                  <div class="metrica-item">
                    <span class="etiqueta">Restantes</span>
                    <span class="valor">{{ totalRows - processedRows }}</span>
                  </div>
                </div>
              </div>
              
              <div v-if="!uploading && progress === 100" class="estado-alerta success mt-4 d-flex align-items-center" style="border-width: 2px;">
                <div class="me-3 fs-3"><i class="bi bi-check-circle-fill text-success"></i></div>
                <div>
                  <h6 class="fw-bold mb-1 text-success">Sincronización Completa</h6>
                  <span class="small text-muted-custom">Se poblaron de datos las 3 tablas de forma automática.</span>
                </div>
              </div>

              <div v-if="!uploading && progress === 0" class="info-espera text-center mt-4">
                <i class="bi bi-hourglass-split mb-2 d-block fs-3 opacity-50 text-muted-custom"></i>
                <span class="small opacity-75 text-muted-custom">Configura el destino y selecciona un archivo para comenzar la transferencia de datos. Las cargas pesadas pueden demorar varios minutos.</span>
              </div>
            </div>
          </div>
        </div>

        <!-- VISTA PREVIA Y MAPEADO DE COLUMNAS -->
        <div class="tarjeta-interfaz tabla-container shadow-soft mt-4" v-if="csvHeaders.length > 0">
          <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-3">
            <h2 class="subtitulo-interfaz m-0">
              <i class="bi bi-table"></i> Verificación de Formato y Sensores
            </h2>
            <span class="badge bg-primary rounded-pill px-4 py-2 fw-bold shadow-sm fs-6">Muestra: 5 filas</span>
          </div>

          <p class="text-muted-custom small mb-4 lh-base">
            TU plataforma cruza el nombre de cada columna con la base de datos. Los datos de estructura se enrutan de forma automática. Si un sensor falla la coincidencia, edita su nombre en la caja correspondiente.
          </p>

          <!-- GUÍA DE CORRECCIÓN DINÁMICA -->
          <div class="guia-correccion mb-4 p-4 rounded-4">
             <h6 class="fw-bold mb-3 d-flex align-items-center gap-2">
               <i class="bi bi-info-circle-fill text-info fs-5"></i>
               Guía de Diccionario de Datos
             </h6>
             <p class="small text-muted-custom mb-3">Copia y pega estas etiquetas exactas en las cajas rojas para corregir los errores de formato:</p>
             
             <div class="d-flex flex-wrap align-items-center gap-2 mb-3">
               <span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 px-3 py-2 fw-bold">Variables de Sistema:</span>
               <span class="badge badge-outline-info">fecha</span>
               <span class="badge badge-outline-info">hora</span>
               <span class="badge badge-outline-info">timestamp</span>
               <span class="badge badge-outline-info">dispositivo</span>
               <span class="badge badge-outline-info">proyecto</span>
               <span class="badge badge-outline-info">id_paquete</span>
             </div>
             
             <div class="d-flex flex-wrap align-items-center gap-2">
               <span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25 px-3 py-2 fw-bold">Sensores del Equipo:</span>
               <span v-for="c in campos" :key="c.id" class="badge badge-outline-success">{{ c.nombre }}</span>
             </div>
          </div>

          <div class="table-responsive table-preview">
            <table class="table-moderna">
              <thead>
                <tr>
                  <th v-for="(header, idx) in csvHeaders" :key="'h-'+idx">
                    <div class="header-editor">
                       <span class="original-header" title="Encabezado original del archivo">{{ headerOriginales[idx] }}</span>
                       <input 
                         type="text" 
                         v-model="csvHeaders[idx]" 
                         class="input-header-edit shadow-sm"
                         :class="claseInputModo(csvHeaders[idx])"
                         title="Edita este nombre para que coincida con la base de datos"
                       >
                       <span v-if="clasificarColumna(csvHeaders[idx]) === 'sistema'" class="status-icon text-info"><i class="bi bi-gear-fill"></i> Dato Sistema</span>
                       <span v-else-if="clasificarColumna(csvHeaders[idx]) === 'sensor'" class="status-icon text-success"><i class="bi bi-check-circle-fill"></i> Sensor Ok</span>
                       <span v-else class="status-icon text-danger"><i class="bi bi-x-circle-fill"></i> Falla Validación</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, rowIndex) in csvPreviewRows" :key="'r-'+rowIndex">
                  <td v-for="(cell, colIndex) in row" :key="'c-'+colIndex">
                    {{ cell }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

const isDark = ref(false);
const isSidebarOpen = ref(true);

const proyectos = ref([]);
const dispositivos = ref([]);
const campos = ref([]);
const proyectoId = ref(null);
const dispositivoId = ref(null);
const loadingProyectos = ref(false);
const loadingDispositivos = ref(false);
const loadingCampos = ref(false);

const file = ref(null);
const fileInput = ref(null);
const rawPreviewText = ref("");
const csvHeaders = ref([]);
const headerOriginales = ref([]);
const csvPreviewRows = ref([]);

const uploading = ref(false);
const progress = ref(0);
const processedRows = ref(0);
const totalRows = ref(0);
const status = ref({ message: '', type: '' });

const baseUrlAPI = typeof window !== 'undefined' && window.API_BASE_URL ? window.API_BASE_URL : 'http://localhost:8001';

const tiempoTranscurrido = ref(0);
const tiempoRestante = ref(0);
let intervalId = null;

const formatoTiempo = (segundosTotales) => {
  if (!segundosTotales || segundosTotales === Infinity || isNaN(segundosTotales)) return "00:00";
  const m = Math.floor(segundosTotales / 60).toString().padStart(2, '0');
  const s = Math.floor(segundosTotales % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

const tiempoTranscurridoFmt = computed(() => formatoTiempo(tiempoTranscurrido.value));
const tiempoRestanteFmt = computed(() => formatoTiempo(tiempoRestante.value));

watch(progress, (nuevoProgreso) => {
  if (nuevoProgreso > 0 && nuevoProgreso < 100) {
    const tiempoPorUnidad = tiempoTranscurrido.value / nuevoProgreso;
    const porcentajeFaltante = 100 - nuevoProgreso;
    tiempoRestante.value = tiempoPorUnidad * porcentajeFaltante;
  } else if (nuevoProgreso === 100) {
    tiempoRestante.value = 0;
  }
});

watch(uploading, (estadoSubida) => {
  if (!estadoSubida) {
    clearInterval(intervalId);
  }
});

const detectarTema = () => {
  if (window.matchMedia) {
    isDark.value = window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
};

const handleThemeChange = (e) => {
  isDark.value = e.matches;
};

const toggleSidebar = () => { 
  isSidebarOpen.value = !isSidebarOpen.value; 
};

const cargarProyectos = async () => {
  loadingProyectos.value = true;
  const token = localStorage.getItem('accessToken');
  const resultadoLocal = JSON.parse(localStorage.getItem('resultado') || '{}');
  const usuarioId = resultadoLocal.usuario?.id;

  if (!token || !usuarioId) {
     loadingProyectos.value = false;
     return; 
  }

  try {
    const response = await fetch(`${baseUrlAPI}/api/proyectos/usuario/${usuarioId}?page=1&limit=100`, { 
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      const res = await response.json();
      proyectos.value = res.data || [];
    }
  } catch (err) {
    console.error("Fallo al descargar proyectos", err);
  } finally {
    loadingProyectos.value = false;
  }
};

const cambiarProyecto = async () => {
  dispositivos.value = [];
  campos.value = [];
  dispositivoId.value = null;
  csvHeaders.value = [];
  csvPreviewRows.value = [];
  file.value = null;
  
  if (!proyectoId.value) return;
  loadingDispositivos.value = true;
  const token = localStorage.getItem('accessToken');

  try {
    const response = await fetch(`${baseUrlAPI}/api/dispositivos/proyecto/${proyectoId.value}?page=1&limit=100`, { 
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) { 
      const res = await response.json();
      dispositivos.value = res.data || [];
    }
  } catch (err) {
    console.error("Fallo al descargar dispositivos", err);
  } finally {
    loadingDispositivos.value = false;
  }
};

const cambiarDispositivo = async () => {
  campos.value = [];
  csvHeaders.value = [];
  csvPreviewRows.value = [];
  file.value = null;

  if (!dispositivoId.value) return;
  loadingCampos.value = true;
  const token = localStorage.getItem('accessToken');

  try {
    const sensoresResponse = await fetch(`${baseUrlAPI}/api/sensores/dispositivo/${dispositivoId.value}?page=1&limit=50`, { 
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    let sensores = [];
    if (sensoresResponse.ok) {
      const res = await sensoresResponse.json();
      sensores = Array.isArray(res) ? res : (res.data || []);
    }

    let todosLosCampos = [];
    for (const sensor of sensores) {
      const camposResponse = await fetch(`${baseUrlAPI}/api/sensores/${sensor.id}/campos`, { 
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (camposResponse.ok) {
        const res = await camposResponse.json();
        const listaCampos = res.campos || (Array.isArray(res) ? res : []);
        
        listaCampos.forEach(c => c.sensor_nombre = sensor.nombre);
        todosLosCampos.push(...listaCampos); 
      }
    }
    campos.value = todosLosCampos;

  } catch (err) {
    console.error("Fallo al descargar campos", err);
  } finally {
    loadingCampos.value = false;
  }
};

const clasificarColumna = (nombreColumna) => {
  if (!nombreColumna) return 'desconocido';
  const nomLower = String(nombreColumna).trim().toLowerCase();
  
  const metadatos = ['fecha', 'hora', 'time', 'timestamp', 'dispositivo', 'proyecto', 'id_paquete'];
  if (metadatos.some(m => nomLower === m || nomLower.includes(m))) return 'sistema';
  
  if (campos.value.some(c => c.nombre.trim().toLowerCase() === nomLower)) return 'sensor';
  
  return 'desconocido';
};

const claseInputModo = (nombreColumna) => {
  const tipo = clasificarColumna(nombreColumna);
  if (tipo === 'sistema') return 'match-sistema';
  if (tipo === 'sensor') return 'match-sensor';
  return 'no-match';
};

const handleFileChange = (e) => {
  const selected = e.target.files[0];
  if (selected && selected.name.endsWith('.csv')) {
    file.value = selected;
    leerMuestraCSV(selected);
    status.value = { message: 'Archivo procesado. Revisa las columnas y realiza ajustes si es necesario.', type: 'info' };
  } else {
    file.value = null;
    csvHeaders.value = [];
    csvPreviewRows.value = [];
    status.value = { message: 'Formato incorrecto. Elige un archivo CSV.', type: 'error' };
  }
};

const leerMuestraCSV = (archivo) => {
  const reader = new FileReader();
  const blobCorte = archivo.slice(0, 10240); 
  
  reader.onload = (e) => {
    rawPreviewText.value = e.target.result;
    const lineas = rawPreviewText.value.split(/\r\n|\n/);
    if (lineas.length > 0) {
      const crudos = lineas[0].split(',');
      headerOriginales.value = crudos.map(h => h.trim());
      csvHeaders.value = crudos.map(h => h.trim()); 

      const filasVisibles = [];
      for (let i = 1; i < Math.min(lineas.length, 6); i++) {
        if (lineas[i].trim().length > 0) {
           filasVisibles.push(lineas[i].split(','));
        }
      }
      csvPreviewRows.value = filasVisibles;
    }
  };
  reader.readAsText(blobCorte);
};

const startUpload = async () => {
  if (!file.value || !dispositivoId.value) return;
  
  uploading.value = true;
  progress.value = 0;
  processedRows.value = 0;
  status.value = { message: 'Extrayendo matriz de datos...', type: 'info' };
  
  tiempoTranscurrido.value = 0;
  tiempoRestante.value = 0;
  clearInterval(intervalId);
  intervalId = setInterval(() => {
    tiempoTranscurrido.value++;
  }, 1000);

  try {
    const textoCompleto = await file.value.text();
    const lineas = textoCompleto.split(/\r\n|\n/).filter(l => l.trim() !== '');
    
    if (lineas.length <= 1) {
        throw new Error("El documento no cuenta con filas de datos válidas.");
    }

    totalRows.value = lineas.length - 1;
    const cabecerasUsuario = csvHeaders.value;
    const BATCH_SIZE = 500;
    let loteActual = [];

    for (let i = 1; i <= totalRows.value; i++) {
        const columnas = lineas[i].split(',');
        
        let carga = {
            proyecto: String(proyectoId.value),
            dispositivo: String(dispositivoId.value),
            fecha: "",
            hora: "",
            id_paquete: i,
            sensores: []
        };
        
        let mapaSensores = {};
        let tieneRegistro = false;

        cabecerasUsuario.forEach((header, indiceCol) => {
            const hCopia = header.trim().toLowerCase();
            const valStr = columnas[indiceCol] ? columnas[indiceCol].trim() : '';

            if (hCopia === 'fecha') carga.fecha = valStr;
            else if (hCopia === 'hora') carga.hora = valStr;
            else if (hCopia === 'id_paquete') carga.id_paquete = parseInt(valStr) || i;
            else if (hCopia === 'timestamp') {
                if (valStr.includes(' ')) {
                    const partes = valStr.split(' ');
                    carga.fecha = partes[0];
                    carga.hora = partes[1];
                } else if (valStr.includes('T')) {
                    const partesT = valStr.split('T');
                    carga.fecha = partesT[0];
                    carga.hora = partesT[1].split('.')[0];
                }
            } else {
                const modeloCampo = campos.value.find(c => c.nombre.trim().toLowerCase() === hCopia);
                if (modeloCampo) {
                    const nomSensor = modeloCampo.sensor_nombre;
                    if (!mapaSensores[nomSensor]) {
                        mapaSensores[nomSensor] = {};
                    }
                    mapaSensores[nomSensor][modeloCampo.nombre] = parseFloat(valStr) || 0.0;
                    tieneRegistro = true;
                }
            }
        });

        if (!carga.fecha) {
            const momentoLocal = new Date();
            carga.fecha = momentoLocal.toISOString().split('T')[0];
            carga.hora = momentoLocal.toTimeString().split(' ')[0];
        }
        
        for (const [nomSensor, dicDatos] of Object.entries(mapaSensores)) {
            carga.sensores.push({ nombre: nomSensor, datos: dicDatos });
        }

        if (tieneRegistro) {
            loteActual.push(carga);
        }

        if (loteActual.length === BATCH_SIZE || i === totalRows.value) {
            if (loteActual.length > 0) {
                const token = localStorage.getItem('accessToken');
                const respuestaApi = await fetch(`${baseUrlAPI}/api/guardar_lote_json/`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(loteActual)
                });
                
                if (!respuestaApi.ok) {
                    throw new Error(`Detención forzada: Error del servidor HTTP ${respuestaApi.status}`);
                }
                
                processedRows.value += loteActual.length;
                progress.value = Math.floor((processedRows.value / totalRows.value) * 100);
                loteActual = [];
            }
        }
    }

    status.value = { message: 'El bloque de datos se sincronizó con el motor correctamente.', type: 'success' };

  } catch (error) {
    console.error("Colapso en la transferencia de lote", error);
    status.value = { message: `Fallo de conexión en proceso: ${error.message}`, type: 'error' };
  } finally {
    uploading.value = false;
    clearInterval(intervalId);
  }
};

onMounted(() => {
  detectarTema();
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', handleThemeChange);
  }
  cargarProyectos();
});

onBeforeUnmount(() => {
  clearInterval(intervalId);
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', handleThemeChange);
  }
});
</script>

<style scoped lang="scss">
$DEEP-NAVY: #0f111a;
$CARD-NAVY: #161925;
$PURPLE-ACCENT: #8A2BE2;
$CYAN-ACCENT: #1ABC9C;
$BLUE-SYSTEM: #3b82f6;
$RED-ERROR: #ef4444;

.plataforma-layout { 
  display: flex; width: 100%; min-height: 100vh; transition: background-color 0.4s ease; background-color: #f8fafc;
  &.theme-dark { background-color: $DEEP-NAVY; }
}

.plataforma-contenido { 
  flex-grow: 1; padding: 40px; margin-left: 80px; transition: margin-left 0.3s; 
  &.shifted { margin-left: 280px; }
}

.carga-masiva-wrapper { max-width: 1400px; margin: 0 auto; padding-bottom: 50px; }

.header-dashboard {
  display: flex; justify-content: space-between; align-items: center; padding: 24px 30px; border-radius: 20px; flex-wrap: wrap; gap: 20px; background: #ffffff; border: 1px solid rgba(0, 0, 0, 0.05); transition: background-color 0.4s ease, border-color 0.4s ease;
}
.theme-dark .header-dashboard { background: $CARD-NAVY; border-color: rgba(255, 255, 255, 0.05); }

.main-title { font-size: 1.6rem; font-weight: 900; margin: 0; color: #1e293b; transition: color 0.4s ease; }
.theme-dark .main-title { color: #ffffff; }

.text-muted-custom { color: #64748b; font-weight: 500; transition: color 0.4s ease; }
.theme-dark .text-muted-custom { color: #cbd5e1; }

.header-selectors { display: flex; gap: 16px; flex-wrap: wrap; }
.input-compact {
  display: flex; align-items: center; padding: 12px 20px; border-radius: 14px; gap: 12px; transition: all 0.3s ease; background: #f1f5f9; border: 1px solid rgba(0,0,0,0.03);
}
.theme-dark .input-compact { background: rgba(0,0,0,0.2); border-color: rgba(255, 255, 255, 0.05); }
.input-compact:focus-within { border-color: $PURPLE-ACCENT; box-shadow: 0 0 0 3px rgba(138, 43, 226, 0.2); }

.icon-purple { color: $PURPLE-ACCENT; font-size: 1.2rem; }
.select-invisible { border: none; background: transparent; font-weight: 800; outline: none; font-size: 0.95rem; width: 200px; color: #1e293b; cursor: pointer; transition: color 0.4s ease; }
.theme-dark .select-invisible { color: #ffffff; }
.theme-dark .select-invisible option { background: $CARD-NAVY; color: #ffffff; }

.grid-configuracion { display: grid; grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); gap: 24px; }

.tarjeta-interfaz {
  background: #ffffff; padding: 32px; border-radius: 20px; border: 1px solid rgba(0, 0, 0, 0.05); height: 100%; display: flex; flex-direction: column; transition: background-color 0.4s ease, border-color 0.4s ease;
  .subtitulo-interfaz { font-size: 1.25rem; font-weight: 900; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; color: $PURPLE-ACCENT; }
}
.theme-dark .tarjeta-interfaz { background: $CARD-NAVY; border-color: rgba(255, 255, 255, 0.05); }
.shadow-soft { box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.05); }

.area-soltar {
  flex-grow: 1; border: 2px dashed rgba(138, 43, 226, 0.3); border-radius: 16px; padding: 50px 20px; text-align: center; cursor: pointer; transition: all 0.3s ease; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 15px; background: rgba(138, 43, 226, 0.02); min-height: 200px;
  .icono-soltar i { font-size: 3rem; opacity: 0.5; color: $PURPLE-ACCENT; transition: all 0.3s ease; }
  .texto-soltar { font-size: 1rem; font-weight: 700; opacity: 0.7; color: #1e293b; transition: color 0.4s ease; }
  &:hover { background: rgba(138, 43, 226, 0.08); border-color: $PURPLE-ACCENT; .icono-soltar i { opacity: 1; transform: translateY(-5px); } }
  &.archivo-listo {
    border-style: solid; border-color: $CYAN-ACCENT; background: rgba(26, 188, 156, 0.05);
    .icono-soltar i { color: $CYAN-ACCENT; opacity: 1; }
    .nombre-archivo { color: $CYAN-ACCENT; font-weight: 900; font-size: 1.1rem; }
  }
}
.theme-dark .area-soltar .texto-soltar { color: #ffffff; }

.ejecucion-body { flex-grow: 1; display: flex; flex-direction: column; justify-content: center; }

.btn-ejecutar {
  width: 100%; padding: 20px; border-radius: 16px; border: none; background: linear-gradient(135deg, #6F00FF, #A300FF); color: #ffffff; font-weight: 900; font-size: 1.1rem; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 12px; transition: all 0.3s ease; box-shadow: 0 10px 20px -5px rgba(138, 43, 226, 0.5);
  &:hover:not(:disabled) { transform: translateY(-3px); filter: brightness(1.15); box-shadow: 0 15px 25px -5px rgba(138, 43, 226, 0.6); }
  &:disabled { background: #94a3b8; box-shadow: none; cursor: not-allowed; opacity: 0.5; }
}

.progreso-contenedor {
  margin-top: 30px;
  .meta-progreso { display: flex; justify-content: space-between; font-size: 0.95rem; font-weight: 800; color: $PURPLE-ACCENT; margin-bottom: 12px; }
  .barra-base { width: 100%; height: 14px; background: rgba(0, 0, 0, 0.05); border-radius: 7px; overflow: hidden; transition: background-color 0.4s ease; }
  .barra-relleno { height: 100%; background: linear-gradient(90deg, $PURPLE-ACCENT 0%, $CYAN-ACCENT 100%); transition: width 0.4s ease; }
}
.theme-dark .barra-base { background: rgba(255, 255, 255, 0.1); }

.tiempo-estimado {
  background: rgba(138, 43, 226, 0.05);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(138, 43, 226, 0.1);
}

.detalles-progreso {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;
  .metrica-item {
    background: #f8fafc; padding: 16px; border-radius: 14px; text-align: center; border: 1px solid rgba(0,0,0,0.02); transition: background-color 0.4s ease, border-color 0.4s ease;
    .etiqueta { display: block; font-size: 0.8rem; font-weight: 900; color: #64748b; text-transform: uppercase; margin-bottom: 6px; letter-spacing: 0.5px; }
    .valor { font-size: 1.4rem; font-weight: 900; color: #1e293b; transition: color 0.4s ease; }
  }
}
.theme-dark .metrica-item { background: rgba(0,0,0,0.2); border-color: rgba(255,255,255,0.05); .valor { color: #ffffff; } }

.estado-alerta {
  margin-top: 20px; padding: 16px 20px; border-radius: 12px; font-size: 0.95rem; font-weight: 800; display: flex; align-items: center; gap: 12px;
  &.success { background: rgba(26, 188, 156, 0.1); color: $CYAN-ACCENT; border: 1px solid rgba(26, 188, 156, 0.2); }
  &.error { background: rgba(231, 76, 60, 0.1); color: $RED-ERROR; border: 1px solid rgba(231, 76, 60, 0.2); }
  &.info { background: rgba(59, 130, 246, 0.1); color: $BLUE-SYSTEM; border: 1px solid rgba(59, 130, 246, 0.2); }
}

.spinner-carga { width: 22px; height: 22px; border: 3px solid #ffffff; border-top-color: transparent; border-radius: 50%; animation: rotar 0.8s linear infinite; }
@keyframes rotar { to { transform: rotate(360deg); } }

/* GUÍA DE CORRECCIÓN */
.guia-correccion {
  background: #ffffff;
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
  transition: all 0.4s ease;
}
.theme-dark .guia-correccion {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.05);
  box-shadow: none;
}

.badge-outline-info { border: 1px solid rgba(59, 130, 246, 0.3); color: #3b82f6; background: rgba(59, 130, 246, 0.05); padding: 6px 12px; font-weight: 700; }
.badge-outline-success { border: 1px solid rgba(26, 188, 156, 0.3); color: #1ABC9C; background: rgba(26, 188, 156, 0.05); padding: 6px 12px; font-weight: 700; }

/* TABLA PREVIEW */
.table-preview { max-height: 450px; overflow-y: auto; overflow-x: auto; border-radius: 14px; border: 1px solid rgba(0,0,0,0.05); transition: border-color 0.4s ease; }
.theme-dark .table-preview { border-color: rgba(255,255,255,0.05); }

.table-moderna {
  width: 100%; border-collapse: collapse; text-align: left;
  thead th { background: #f1f5f9; padding: 18px 24px; border-bottom: 2px solid rgba(0,0,0,0.05); position: sticky; top: 0; z-index: 10; transition: background-color 0.4s ease, border-color 0.4s ease; }
  tbody td { padding: 14px 24px; border-bottom: 1px solid rgba(0,0,0,0.03); font-size: 0.95rem; color: #475569; font-weight: 600; white-space: nowrap; transition: border-color 0.4s ease, color 0.4s ease; }
}
.theme-dark .table-moderna {
  thead th { background: #1a1a2e; border-bottom-color: rgba(255,255,255,0.1); }
  tbody td { border-bottom-color: rgba(255,255,255,0.02); color: #cbd5e1; }
}

.header-editor {
  display: flex; flex-direction: column; gap: 8px; min-width: 160px;
  .original-header { font-size: 0.75rem; color: #64748b; font-weight: 900; text-transform: uppercase; letter-spacing: 1px; transition: color 0.4s ease; }
  
  .input-header-edit {
    padding: 10px 14px; border-radius: 10px; border: 2px solid transparent; outline: none; font-weight: 800; font-size: 0.95rem; transition: all 0.3s ease; color: #1e293b;
    background: #ffffff;
    &.match-sensor { border-color: $CYAN-ACCENT; background: rgba(26, 188, 156, 0.05); }
    &.match-sistema { border-color: $BLUE-SYSTEM; background: rgba(59, 130, 246, 0.05); }
    &.no-match { border-color: $RED-ERROR; background: rgba(231, 76, 60, 0.05); }
    &:focus { box-shadow: 0 0 0 4px rgba(0,0,0,0.05); }
  }
  
  .status-icon { font-size: 0.8rem; font-weight: 900; display: flex; align-items: center; gap: 6px; }
}
.theme-dark .header-editor .input-header-edit { background: $CARD-NAVY; color: #ffffff; }
.theme-dark .header-editor .original-header { color: #94a3b8; }

@media (max-width: 768px) {
  .plataforma-contenido { margin-left: 0; padding: 20px; }
  .grid-configuracion { grid-template-columns: 1fr; }
  .header-dashboard { flex-direction: column; align-items: stretch; }
  .header-selectors { flex-direction: column; }
  .input-compact { width: 100%; }
}
</style>