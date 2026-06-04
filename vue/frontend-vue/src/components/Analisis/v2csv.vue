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
        <div class="header-dashboard glass-panel shadow-soft mb-4">
          <div class="header-titles">
            <h2 class="main-title">Enrutamiento de Datos</h2>
            <span class="sub-title text-muted">Selecciona el destino de TU información</span>
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
              <i class="bi bi-cloud-upload"></i>
              <span v-if="!file">Haz clic para seleccionar el archivo CSV</span>
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
            <button 
              @click="startUpload" 
              :disabled="!file || !dispositivoId || uploading"
              class="btn-ejecutar"
            >
              <i v-if="!uploading" class="bi bi-play-circle-fill"></i>
              <span v-else class="spinner-carga"></span>
              {{ uploading ? 'Enviando Lotes...' : 'Iniciar Sincronización Masiva' }}
            </button>

            <div v-if="uploading || progress > 0" class="progreso-contenedor">
              <div class="meta-progreso">
                <span>Sincronizando bloque de datos históricos</span>
                <span>{{ progress }}%</span>
              </div>
              <div class="barra-base">
                <div class="barra-relleno" :style="{ width: progress + '%' }"></div>
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
          </div>
        </div>

        <!-- VISTA PREVIA Y MAPEADO DE COLUMNAS -->
        <div class="tarjeta-interfaz shadow-soft mt-4" v-if="csvHeaders.length > 0">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h2 class="subtitulo-interfaz m-0">
              <i class="bi bi-table"></i> Vista Previa y Verificación de Sensores
            </h2>
            <span class="badge bg-primary rounded-pill">Muestra: 5 filas</span>
          </div>

          <p class="text-muted small mb-4">
            El sistema compara los nombres de tus columnas con los sensores registrados en la base de datos. Si un nombre no coincide, edítalo directamente en la caja de texto inferior.
          </p>

          <div class="table-responsive table-preview">
            <table class="table-moderna">
              <thead>
                <!-- Fila de Inputs Mapeadores -->
                <tr>
                  <th v-for="(header, idx) in csvHeaders" :key="'h-'+idx">
                    <div class="header-editor">
                       <span class="original-header" title="Encabezado original del archivo">{{ headerOriginales[idx] }}</span>
                       <input 
                         type="text" 
                         v-model="csvHeaders[idx]" 
                         class="input-header-edit"
                         :class="{ 'match': verificaCampo(csvHeaders[idx]), 'no-match': !verificaCampo(csvHeaders[idx]) }"
                         title="Edita este nombre para que coincida con la base de datos"
                       >
                       <span v-if="verificaCampo(csvHeaders[idx])" class="status-icon text-success"><i class="bi bi-check-circle-fill"></i> Ok</span>
                       <span v-else class="status-icon text-danger"><i class="bi bi-x-circle-fill"></i> Falla</span>
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
import { ref, computed, onMounted } from 'vue';
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import { uploadState, iniciarSubidaGlobal } from '@/stores/uploadStore.js'; 

const props = defineProps({ 
  isDark: { type: Boolean, default: true } 
});

const isSidebarOpen = ref(true);

// Variables de Selección
const proyectos = ref([]);
const dispositivos = ref([]);
const campos = ref([]);
const proyectoId = ref(null);
const dispositivoId = ref(null);
const loadingProyectos = ref(false);
const loadingDispositivos = ref(false);
const loadingCampos = ref(false);

// Variables de Archivo y Previa
const file = ref(null);
const fileInput = ref(null);
const rawPreviewText = ref("");
const firstLineEndIndex = ref(0);
const csvHeaders = ref([]);
const headerOriginales = ref([]);
const csvPreviewRows = ref([]);

// Estado Global
const uploading = computed(() => uploadState.uploading);
const progress = computed(() => uploadState.progress);
const processedRows = computed(() => uploadState.processedRows);
const totalRows = computed(() => uploadState.totalRows);
const status = computed(() => uploadState.status);
const baseUrlAPI = typeof window !== 'undefined' && window.API_BASE_URL ? window.API_BASE_URL : 'http://localhost:8001';

const toggleSidebar = () => { 
  isSidebarOpen.value = !isSidebarOpen.value; 
};

// --- RUTINAS DE EXTRACCIÓN (IDÉNTICAS A HISTÓRICOS) ---

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

const verificaCampo = (nombreColumna) => {
  const nomLower = String(nombreColumna).trim().toLowerCase();
  // Toleramos 'fecha_hora_lectura', 'timestamp', 'fecha' como válidos por defecto
  if (nomLower.includes('fecha') || nomLower.includes('time')) return true;
  // Buscamos coincidencia en la base de datos
  return campos.value.some(c => c.nombre.trim().toLowerCase() === nomLower);
};

// --- RUTINAS DE ARCHIVO ---

const handleFileChange = (e) => {
  const selected = e.target.files[0];
  if (selected && selected.name.endsWith('.csv')) {
    file.value = selected;
    leerMuestraCSV(selected);
    uploadState.status = { message: 'Archivo procesado en memoria local. Verifica las columnas.', type: 'info' };
  } else {
    file.value = null;
    csvHeaders.value = [];
    csvPreviewRows.value = [];
    uploadState.status = { message: 'Debes elegir un archivo con formato CSV.', type: 'error' };
  }
};

const leerMuestraCSV = (archivo) => {
  const reader = new FileReader();
  // Leemos solo los primeros 10KB para evitar colapsar la RAM con archivos inmensos
  const blobCorte = archivo.slice(0, 10240); 
  
  reader.onload = (e) => {
    rawPreviewText.value = e.target.result;
    
    // Detectamos saltos de linea
    const lineas = rawPreviewText.value.split(/\r\n|\n/);
    if (lineas.length > 0) {
      firstLineEndIndex.value = rawPreviewText.value.indexOf('\n');
      
      const crudos = lineas[0].split(',');
      headerOriginales.value = crudos.map(h => h.trim());
      csvHeaders.value = crudos.map(h => h.trim()); // Copia editable

      const filasVisibles = [];
      // Tomamos maximo 5 lineas de datos reales
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

const generarArchivoModificado = () => {
  const cabeceraEditada = csvHeaders.value.join(',') + '\n';
  const restoDelArchivo = file.value.slice(firstLineEndIndex.value + 1);
  return new File([cabeceraEditada, restoDelArchivo], file.value.name, { type: 'text/csv' });
};

const startUpload = () => {
  if (!file.value || !dispositivoId.value) return;
  const archivoFinal = generarArchivoModificado();
  iniciarSubidaGlobal(archivoFinal, proyectoId.value, dispositivoId.value);
};

onMounted(() => {
  cargarProyectos();
});
</script>

<style scoped lang="scss">
.carga-masiva-wrapper {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ENRUTAMIENTO (Extraído de VistaReportes) */
.header-dashboard {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 25px;
  border-radius: 16px;
  flex-wrap: wrap;
  gap: 20px;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.05);
}
.theme-dark .header-dashboard {
  background: #2B2B40;
  border-color: rgba(255, 255, 255, 0.05);
}
.main-title { font-size: 1.5rem; font-weight: 800; margin: 0; color: #1e293b; }
.theme-dark .main-title { color: white; }
.sub-title { font-size: 0.85rem; font-weight: 600; }

.header-selectors { display: flex; gap: 12px; }
.input-compact {
  display: flex; align-items: center; padding: 10px 18px; border-radius: 12px; gap: 10px; transition: all 0.2s;
  background: #f8fafc; border: 1px solid rgba(0,0,0,0.05);
}
.theme-dark .input-compact { background: rgba(0,0,0,0.2); border-color: rgba(255, 255, 255, 0.05); }
.input-compact:focus-within { border-color: #8A2BE2; box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.3); }

.icon-purple { color: #8A2BE2; font-size: 1.2rem; }
.select-invisible { border: none; background: transparent; font-weight: 700; outline: none; font-size: 0.95rem; width: 180px; color: #1e293b; }
.theme-dark .select-invisible { color: white; }
.theme-dark .select-invisible option { background: #161925; color: white; }

/* GRID PRINCIPAL */
.grid-configuracion {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
}

.tarjeta-interfaz {
  background: white;
  padding: 30px;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.05);

  .subtitulo-interfaz {
    font-size: 1.2rem;
    font-weight: 800;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #8A2BE2;
  }
}

.theme-dark .tarjeta-interfaz { background: #2B2B40; border-color: rgba(255, 255, 255, 0.05); }
.shadow-soft { box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03); }

/* AREA UPLOAD */
.area-soltar {
  border: 2px dashed rgba(138, 43, 226, 0.3);
  border-radius: 14px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  background: rgba(138, 43, 226, 0.02);

  i { font-size: 2.5rem; opacity: 0.5; color: #8A2BE2; transition: all 0.3s; }
  span { font-size: 0.95rem; font-weight: 600; opacity: 0.7; color: #1e293b; }

  &:hover { background: rgba(138, 43, 226, 0.08); border-color: #8A2BE2; i { opacity: 1; transform: scale(1.1); } }
  &.archivo-listo {
    border-style: solid; border-color: #1ABC9C; background: rgba(26, 188, 156, 0.05);
    i { color: #1ABC9C; opacity: 1; }
    .nombre-archivo { color: #1ABC9C; font-weight: 800; }
  }
}
.theme-dark .area-soltar span { color: white; }

.seccion-ejecucion { display: flex; flex-direction: column; justify-content: center; }

.btn-ejecutar {
  width: 100%;
  padding: 18px;
  border-radius: 14px;
  border: none;
  background: linear-gradient(to right, #6F00FF, #A300FF);
  color: white;
  font-weight: 800;
  font-size: 1.05rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(138, 43, 226, 0.35);
  &:hover:not(:disabled) { transform: translateY(-2px); filter: brightness(1.15); }
  &:disabled { background: #94a3b8; box-shadow: none; cursor: not-allowed; opacity: 0.6; }
}

.progreso-contenedor {
  margin-top: 30px;
  .meta-progreso { display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 800; color: #8A2BE2; margin-bottom: 12px; }
  .barra-base { width: 100%; height: 12px; background: rgba(0, 0, 0, 0.05); border-radius: 6px; overflow: hidden; }
  .barra-relleno { height: 100%; background: linear-gradient(90deg, #8A2BE2 0%, #1ABC9C 100%); transition: width 0.4s ease; }
}
.theme-dark .barra-base { background: rgba(255, 255, 255, 0.1); }

.detalles-progreso {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 15px;
  .metrica-item {
    background: #f8fafc; padding: 14px; border-radius: 12px; text-align: center; border: 1px solid rgba(0,0,0,0.02);
    .etiqueta { display: block; font-size: 0.75rem; font-weight: 800; color: #64748b; text-transform: uppercase; margin-bottom: 4px; }
    .valor { font-size: 1.2rem; font-weight: 900; color: #1e293b; }
  }
}
.theme-dark .metrica-item { background: rgba(0,0,0,0.2); border-color: rgba(255,255,255,0.05); .valor { color: white; } }

.estado-alerta {
  margin-top: 15px; padding: 12px 16px; border-radius: 10px; font-size: 0.9rem; font-weight: 700; display: flex; align-items: center; gap: 10px;
  &.success { background: rgba(26, 188, 156, 0.1); color: #1ABC9C; border: 1px solid rgba(26, 188, 156, 0.2); }
  &.error { background: rgba(231, 76, 60, 0.1); color: #E74C3C; border: 1px solid rgba(231, 76, 60, 0.2); }
  &.info { background: rgba(52, 152, 219, 0.1); color: #3498DB; border: 1px solid rgba(52, 152, 219, 0.2); }
}

.spinner-carga { width: 18px; height: 18px; border: 3px solid white; border-top-color: transparent; border-radius: 50%; animation: rotar 0.8s linear infinite; }
@keyframes rotar { to { transform: rotate(360deg); } }

/* TABLA PREVIEW */
.table-preview { max-height: 400px; overflow-y: auto; border-radius: 12px; border: 1px solid rgba(0,0,0,0.05); }
.theme-dark .table-preview { border-color: rgba(255,255,255,0.05); }

.table-moderna {
  width: 100%; border-collapse: collapse; text-align: left;
  thead th { background: #f8fafc; padding: 12px; border-bottom: 2px solid rgba(0,0,0,0.05); position: sticky; top: 0; z-index: 10; }
  tbody td { padding: 10px 12px; border-bottom: 1px solid rgba(0,0,0,0.03); font-size: 0.85rem; color: #475569; font-weight: 600; white-space: nowrap; }
}
.theme-dark .table-moderna {
  thead th { background: #161925; border-bottom-color: rgba(255,255,255,0.1); }
  tbody td { border-bottom-color: rgba(255,255,255,0.02); color: #cbd5e1; }
}

.header-editor {
  display: flex; flex-direction: column; gap: 6px;
  .original-header { font-size: 0.65rem; color: #94a3b8; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
  .input-header-edit {
    padding: 6px 10px; border-radius: 6px; border: 2px solid transparent; outline: none; font-weight: 700; font-size: 0.85rem; background: white; transition: all 0.2s; color: #1e293b;
    &.match { border-color: #1ABC9C; background: rgba(26, 188, 156, 0.05); }
    &.no-match { border-color: #E74C3C; background: rgba(231, 76, 60, 0.05); }
    &:focus { box-shadow: 0 0 0 3px rgba(0,0,0,0.05); }
  }
  .status-icon { font-size: 0.7rem; font-weight: 800; display: flex; align-items: center; gap: 4px; }
}
.theme-dark .header-editor .input-header-edit { background: #2B2B40; color: white; }
</style>