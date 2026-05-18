<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma 
        titulo="Sincronización de Historial IoT"
        subtitulo="Gestión masiva de datos mediante procesamiento por lotes (Vista Prueba)"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="carga-masiva-wrapper">
        <div class="grid-configuracion">
          
          <div class="tarjeta-interfaz">
            <h2 class="subtitulo-interfaz">
              <i class="bi bi-gear-fill"></i> Parámetros de Destino
            </h2>
            
            <div class="campo-formulario">
              <label>ID del Proyecto</label>
              <div class="input-con-icono">
                <i class="bi bi-folder-fill"></i>
                <input 
                  type="text" 
                  v-model="proyectoId" 
                  placeholder="Ej. 2"
                  class="input-estilizado"
                >
              </div>
            </div>

            <div class="campo-formulario">
              <label>ID del Dispositivo</label>
              <div class="input-con-icono">
                <i class="bi bi-cpu-fill"></i>
                <input 
                  type="text" 
                  v-model="dispositivoId" 
                  placeholder="Ej. 12"
                  class="input-estilizado"
                >
              </div>
            </div>
            
            <p class="nota-informativa">
              TÚ defines el destino de los datos. Verifica los IDs en TU base de datos para asegurar la relación correcta.
            </p>
          </div>

          <div class="tarjeta-interfaz">
            <h2 class="subtitulo-interfaz">
              <i class="bi bi-file-earmark-arrow-up-fill"></i> Fuente de Datos
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
        </div>

        <div class="tarjeta-interfaz seccion-ejecucion">
          <button 
            @click="startUpload" 
            :disabled="!file || uploading"
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
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'; // 🟢 Agregamos 'computed'
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

// Importamos el estado global
import { uploadState, iniciarSubidaGlobal } from '@/stores/uploadStore.js'; 

const props = defineProps({ 
  isDark: { type: Boolean, default: false } 
});

const isSidebarOpen = ref(true);
const file = ref(null);
const fileInput = ref(null);
const proyectoId = ref("2");
const dispositivoId = ref("12");

// 🟢 SOLUCIÓN: Conectamos el estado global con la vista local para que el HTML no falle
const uploading = computed(() => uploadState.uploading);
const progress = computed(() => uploadState.progress);
const processedRows = computed(() => uploadState.processedRows);
const totalRows = computed(() => uploadState.totalRows);
const status = computed(() => uploadState.status);

const toggleSidebar = () => { 
  isSidebarOpen.value = !isSidebarOpen.value; 
};

const handleFileChange = (e) => {
  const selected = e.target.files[0];
  if (selected && selected.name.endsWith('.csv')) {
    file.value = selected;
    uploadState.status = { message: 'Archivo cargado. Listo para sincronizar.', type: 'info' };
  } else {
    file.value = null;
    uploadState.status = { message: 'Debes elegir un archivo con formato CSV.', type: 'error' };
  }
};

const startUpload = () => {
  if (!file.value) return;
  // Disparamos la función global y le pasamos los datos
  iniciarSubidaGlobal(file.value, proyectoId.value, dispositivoId.value);
};
</script>

<style scoped lang="scss">
.carga-masiva-wrapper {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.grid-configuracion {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
  margin-bottom: 25px;
}

.tarjeta-interfaz {
  background: white;
  padding: 30px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);

  .subtitulo-interfaz {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: #8A2BE2;
  }
}

.campo-formulario {
  margin-bottom: 15px;
  label {
    display: block;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 8px;
    opacity: 0.8;
  }
}

.input-con-icono {
  position: relative;
  display: flex;
  align-items: center;
  i { position: absolute; left: 15px; opacity: 0.4; }
  .input-estilizado {
    width: 100%;
    padding: 12px 15px 12px 45px;
    border-radius: 10px;
    border: 1px solid rgba(0, 0, 0, 0.1);
    outline: none;
    transition: all 0.2s;
    &:focus { border-color: #8A2BE2; box-shadow: 0 0 0 3px rgba(138, 43, 226, 0.1); }
  }
}

.area-soltar {
  border: 2px dashed rgba(138, 43, 226, 0.2);
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: rgba(138, 43, 226, 0.02);

  i { font-size: 2.5rem; opacity: 0.3; color: #8A2BE2; }
  span { font-size: 0.9rem; font-weight: 500; opacity: 0.6; }

  &:hover { background: rgba(138, 43, 226, 0.05); border-color: #8A2BE2; i { opacity: 0.7; } }
  &.archivo-listo {
    border-style: solid; border-color: #1ABC9C; background: rgba(26, 188, 156, 0.05);
    i { color: #1ABC9C; opacity: 1; }
    .nombre-archivo { color: #1ABC9C; font-weight: 700; }
  }
}

.nota-informativa { font-size: 0.8rem; margin-top: 15px; opacity: 0.6; font-style: italic; }

.seccion-ejecucion { margin-top: 25px; }

.btn-ejecutar {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  border: none;
  background: #8A2BE2;
  color: white;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s;
  &:hover:not(:disabled) { background: #7B27CB; transform: translateY(-2px); }
  &:disabled { background: #ccc; cursor: not-allowed; }
}

.progreso-contenedor {
  margin-top: 30px;
  .meta-progreso { display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 700; color: #8A2BE2; margin-bottom: 10px; }
  .barra-base { width: 100%; height: 10px; background: rgba(0, 0, 0, 0.05); border-radius: 5px; overflow: hidden; }
  .barra-relleno { height: 100%; background: linear-gradient(90deg, #8A2BE2 0%, #7B27CB 100%); transition: width 0.4s ease; }
}

.detalles-progreso {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-top: 15px;
  .metrica-item {
    background: #f8f9fa; padding: 12px; border-radius: 10px; text-align: center;
    .etiqueta { display: block; font-size: 0.7rem; font-weight: 700; color: #adb5bd; text-transform: uppercase; }
    .valor { font-size: 1.1rem; font-weight: 700; color: #495057; }
  }
}

.estado-alerta {
  margin-top: 15px; padding: 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 8px;
  &.success { background: rgba(26, 188, 156, 0.1); color: #1ABC9C; }
  &.error { background: rgba(231, 76, 60, 0.1); color: #E74C3C; }
  &.info { background: rgba(52, 152, 219, 0.1); color: #3498DB; }
}

.spinner-carga {
  width: 18px; height: 18px; border: 2px solid white; border-top-color: transparent; border-radius: 50%; animation: rotar 0.8s linear infinite;
}

@keyframes rotar { to { transform: rotate(360deg); } }

.theme-dark {
  .tarjeta-interfaz { background: #2B2B40; border-color: rgba(255, 255, 255, 0.05); }
  .input-estilizado { background: #1A1A2E; color: white; border-color: rgba(255, 255, 255, 0.1); }
  .area-soltar { background: rgba(255, 255, 255, 0.02); border-color: rgba(255, 255, 255, 0.1); span { color: white; } }
  .metrica-item { background: #1A1A2E; .valor { color: white; } }
  .barra-base { background: rgba(255, 255, 255, 0.1); }
}
</style>