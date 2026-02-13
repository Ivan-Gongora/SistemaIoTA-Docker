<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma 
        titulo="Monitor en Tiempo Real"
        subtitulo="Supervisión crítica de infraestructura. Visualización de telemetría en vivo con detección de anomalías."
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="reportes-contenido">
        
        <!-- 1. PANEL DE CONTROL UNIFICADO -->
        <div class="control-panel" :class="{ 'theme-dark': isDark }">
            
            <!-- SECCIÓN CONEXIÓN -->
            <div class="control-section">
                <h4 class="section-title"><i class="bi bi-hdd-network"></i> Conexión</h4>
                
                <div class="form-group">
                    <label>Proyecto</label>
                    <div class="input-wrapper">
                        <i class="bi bi-folder2-open input-icon"></i>
                        <select v-model="proyectoSeleccionadoId" @change="cargarDispositivos" class="form-control">
                            <option :value="null" disabled>{{ loadingProyectos ? 'Cargando...' : 'Seleccionar...' }}</option>
                            <option v-for="p in proyectos" :key="p.id" :value="p.id">{{ p.nombre }}</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>Dispositivo</label>
                    <div class="input-wrapper">
                        <i class="bi bi-cpu input-icon"></i>
                        <select v-model="dispositivoSeleccionadoId" @change="cargarCampos" class="form-control" :disabled="!proyectoSeleccionadoId">
                            <option :value="null" disabled>{{ loadingDispositivos ? 'Escaneando...' : 'Seleccionar...' }}</option>
                            <option v-for="d in dispositivos" :key="d.id" :value="d.id">{{ d.nombre }}</option>
                        </select>
                    </div>
                    <!-- INDICADOR DE SALUD -->
                    <div v-if="dispositivoSeleccionadoId" class="health-status" :class="dispositivoOnline ? 'online' : 'offline'">
                        <i class="bi" :class="dispositivoOnline ? 'bi-wifi' : 'bi-wifi-off'"></i>
                        {{ dispositivoOnline ? 'Conectado' : 'Sin señal reciente' }}
                    </div>
                </div>
            </div>

            <!-- SECCIÓN VENTANA DE TIEMPO -->
            <div class="control-section config-section">
                <h4 class="section-title"><i class="bi bi-clock-history"></i> Ventana de Tiempo</h4>
                
                <div class="form-group">
                    <label>Duración Visual</label>
                    <div class="input-wrapper">
                        <i class="bi bi-hourglass-split input-icon"></i>
                        <select v-model="ventanaTiempo" class="form-control" :disabled="!dispositivoSeleccionadoId">
                            <option value="5">Últimos 5 minutos (Live)</option>
                            <option value="60">Última 1 hora</option>
                            <option value="1440">Últimas 24 horas</option>
                        </select>
                    </div>
                    <div class="status-pill" :class="ventanaTiempo <= 5 ? 'live' : 'history'">
                        <i class="bi" :class="ventanaTiempo <= 5 ? 'bi-broadcast' : 'bi-database-check'"></i>
                        <span>{{ ventanaTiempo <= 5 ? 'Transmisión en Vivo' : 'Consulta Histórica' }}</span>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN INTELIGENCIA -->
            <div class="control-section config-section">
                <h4 class="section-title"><i class="bi bi-activity"></i> Inteligencia</h4>
                
                <div class="form-group switch-group">
                    <label>Análisis de Datos</label>
                    <div class="toggle-wrapper">
                        <!-- 🚨 SWITCH QUE CONTROLA LA VARIABLE 'analisisActivo' -->
                        <label class="switch">
                            <input type="checkbox" v-model="analisisActivo" :disabled="!dispositivoSeleccionadoId">
                            <span class="slider round"></span>
                        </label>
                        <span class="switch-label" :class="{ 'active': analisisActivo }">
                            {{ analisisActivo ? 'Activado' : 'Desactivado' }}
                        </span>
                    </div>
                </div>

                <div class="form-group mt-2" v-if="analisisActivo">
                    <label>Sensibilidad</label>
                    <div class="range-wrapper">
                        <input type="range" min="1" max="3" step="1" v-model="sensibilidad" class="form-range">
                        <div class="range-labels">
                            <span>Baja</span><span>Media</span><span>Alta</span>
                        </div>
                    </div>
                </div>
                
                 <button v-if="analisisActivo && dispositivoSeleccionadoId" @click="descargarReporteAnomalias" class="btn-exportar-anomalias">
                    <i class="bi bi-file-earmark-arrow-down"></i> Reporte de Picos
                 </button>
            </div>
        </div>
        
        <!-- TARJETAS DE RESUMEN GLOBAL -->
        <div class="dashboard-mini" v-if="dispositivoSeleccionadoId && !loadingCampos">
            <div class="mini-card">
                <div class="icon-box purple"><i class="bi bi-exclamation-triangle"></i></div>
                <div class="info">
                    <span class="label">Alertas Hoy</span>
                    <span class="value">{{ resumenGlobal.alertas }}</span>
                </div>
            </div>
            <div class="mini-card">
                <div class="icon-box green"><i class="bi bi-activity"></i></div>
                <div class="info">
                    <span class="label">Actividad Total</span>
                    <span class="value">{{ resumenGlobal.actividad }}</span>
                </div>
            </div>
            <div class="mini-card">
                <div class="icon-box blue"><i class="bi bi-clock"></i></div>
                <div class="info">
                    <span class="label">Hora Pico</span>
                    <span class="value">{{ resumenGlobal.horaPico }}</span>
                </div>
            </div>
        </div>
         
        <!-- SELECTOR DE VARIABLES -->
        <div class="variables-panel" v-if="campos.length > 0">
            <div class="panel-header">
                <h4><i class="bi bi-check2-square"></i> Variables Disponibles</h4>
                <span class="subtitle">Seleccione las métricas a monitorear</span>
            </div>
            
            <div v-if="loadingCampos" class="loading-state">
                <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
                <span class="ms-2">Cargando configuración...</span>
            </div>

            <div class="variables-grid">
                <div 
                    v-for="c in campos" 
                    :key="c.id" 
                    class="selectable-card"
                    :class="{ 'selected': camposSeleccionadosIds.includes(c.id) }"
                    @click="toggleCampo(c.id)"
                >
                    <div class="card-icon">
                        <i :class="getIcon(c.magnitud_tipo)"></i>
                    </div>
                    <div class="card-info">
                        <span class="var-name">{{ c.nombre }}</span>
                        <span class="var-unit">{{ c.simbolo_unidad || '-' }}</span>
                    </div>
                    <div class="check-indicator"><i class="bi bi-check-lg"></i></div>
                </div>
            </div>
        </div>
        
        <!-- MENSAJES DE ESTADO -->
        <div v-if="loadingCampos" class="alert-info">
            <i class="bi bi-arrow-clockwise fa-spin"></i> Estableciendo conexión segura...
        </div>
        <div v-else-if="errorCampos" class="alert-box error">
            <i class="bi bi-exclamation-triangle"></i> {{ errorCampos }}
        </div>
        
        <!-- GRID DE GRÁFICOS -->
        <div class="charts-grid-realtime" v-if="camposFiltrados.length > 0">
            <GraficoEnTiempoReal
                v-for="campo in camposFiltrados"
                :key="campo.id"
                :campo-id="campo.id"
                :titulo="campo.nombre"
                :is-dark="isDark"
                :simbolo-unidad="campo.simbolo_unidad || ''"
                :metodo-carga="metodoCarga" 
                :ventana-tiempo="parseInt(ventanaTiempo)"
                
                :analisis-activo="analisisActivo" 
                
                @stats-updated="actualizarResumenGlobal" 
            />  
        </div>
        
      </div>
    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import GraficoEnTiempoReal from '../graficos/GraficoEnTiempoReal.vue'; 



export default {
  name: 'VistaTiempoReal',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
    GraficoEnTiempoReal
  },
  data() {
    return {
      isDark: false, 
      isSidebarOpen: true, 
      
      proyectos: [],
      dispositivos: [],
      campos: [], 
      
      proyectoSeleccionadoId: null,
      dispositivoSeleccionadoId: null,
      camposSeleccionadosIds: [],
      
      // Configuración
      metodoCarga: 'optimizado', 
      ventanaTiempo: '5', 
      analisisActivo: true, // 🚨 Controla el análisis globalmente
      sensibilidad: 2, 

      dispositivoOnline: false,
      resumenGlobal: { alertas: 0, actividad: 0, horaPico: '--:--' },

      loadingProyectos: true,
      loadingDispositivos: false,
      loadingCampos: false,
      errorCampos: null,
      error: null,
    };
  },
  computed: {
    camposFiltrados() {
      return this.campos.filter(c => this.camposSeleccionadosIds.includes(c.id));
    }
  },
  mounted() {
    this.cargarProyectos();
    this.detectarTemaSistema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
    }
  },
  beforeUnmount() { 
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
    }
  },
  methods: {
    toggleCampo(id) {
        const index = this.camposSeleccionadosIds.indexOf(id);
        if (index === -1) {
            this.camposSeleccionadosIds.push(id);
        } else {
            this.camposSeleccionadosIds.splice(index, 1);
        }
    },

    actualizarResumenGlobal(statsHijo) {
        if (statsHijo.esMovimiento) {
             this.resumenGlobal.actividad = statsHijo.totalEventos;
        }
    },

    async verificarSaludDispositivo() {
        if (!this.dispositivoSeleccionadoId) return;
        const token = localStorage.getItem('accessToken');
        try {
             if (this.campos.length > 0) {
                 const campoId = this.campos[0].id;
                 const response = await fetch(`${API_BASE_URL}/api/valores/ultimo/${campoId}`, { 
                     headers: { 'Authorization': `Bearer ${token}` } 
                 });
                 if (response.ok) {
                     const data = await response.json();
                     const ultimaFecha = new Date(data.fecha_hora_lectura);
                     this.dispositivoOnline = (new Date() - ultimaFecha) < (5 * 60 * 1000);
                 }
             }
        } catch (e) { console.error("Error salud:", e); }
    },

    descargarReporteAnomalias() {
        alert("Generando reporte de picos para las últimas 24 horas... (Funcionalidad Backend Pendiente)");
    },
    
    // --- CARGA DE DATOS ---
    async cargarProyectos() {
      this.loadingProyectos = true;
      const token = localStorage.getItem('accessToken');
      const resultado = JSON.parse(localStorage.getItem('resultado') || '{}');
      const usuarioId = resultado.usuario?.id;

      if (!token || !usuarioId) { 
        this.$router.push('/'); return; 
      }

      const params = new URLSearchParams({ page: 1, limit: 100 });

      try {
        const response = await fetch(`${API_BASE_URL}/api/proyectos/usuario/${usuarioId}?${params}`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (response.ok) {
            const jsonResponse = await response.json();
            this.proyectos = jsonResponse.data || [];
            
            if (this.proyectos.length > 0) {
                this.proyectoSeleccionadoId = this.proyectos[0].id;
                await this.cargarDispositivos(); 
            }
        }
      } catch (err) {
        console.error(err);
      } finally {
        this.loadingProyectos = false;
      }
    },

    async cargarDispositivos() {
      this.loadingDispositivos = true;
      this.dispositivos = []; 
      this.campos = [];
      this.dispositivoSeleccionadoId = null;
      this.camposSeleccionadosIds = [];
      
      const token = localStorage.getItem('accessToken');
      if (!this.proyectoSeleccionadoId) return;
      
      const params = new URLSearchParams({ page: 1, limit: 100 });

      try {
        const response = await fetch(`${API_BASE_URL}/api/dispositivos/proyecto/${this.proyectoSeleccionadoId}?${params}`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        if (response.ok) { 
            const jsonResponse = await response.json();
            this.dispositivos = jsonResponse.data || []; 
        }
        
        if (this.dispositivos.length > 0) {
          this.dispositivoSeleccionadoId = this.dispositivos[0].id;
          await this.cargarCampos(); 
        }
      } catch (err) {
        console.error(err);
      } finally {
        this.loadingDispositivos = false;
      }
    },
    
    async cargarCampos() {
      this.loadingCampos = true;
      this.errorCampos = null;
      this.campos = [];
      this.camposSeleccionadosIds = [];
      
      const token = localStorage.getItem('accessToken');
      if (!this.dispositivoSeleccionadoId) return;

      try {
        const params = new URLSearchParams({ page: 1, limit: 50 });
        const sensoresResponse = await fetch(`${API_BASE_URL}/api/sensores/dispositivo/${this.dispositivoSeleccionadoId}?${params}`, { 
          headers: { 'Authorization': `Bearer ${token}` } 
        });
        
        let sensores = [];
        if (sensoresResponse.ok) {
            const sensoresData = await sensoresResponse.json();
            sensores = Array.isArray(sensoresData) ? sensoresData : (sensoresData.data || []);
        }

        let todosLosCampos = [];
        for (const sensor of sensores) {
          const camposResponse = await fetch(`${API_BASE_URL}/api/sensores/${sensor.id}/campos`, { 
            headers: { 'Authorization': `Bearer ${token}` } 
          });
          
          if (camposResponse.ok) {
            const camposData = await camposResponse.json();
            const listaCampos = camposData.campos || (Array.isArray(camposData) ? camposData : []);
            todosLosCampos.push(...listaCampos); 
          }
        }
        
        this.campos = todosLosCampos;
        
        this.verificarSaludDispositivo();

      } catch (err) {
        console.error("Error cargando campos:", err);
        this.errorCampos = 'Error al cargar configuración.';
      } finally {
        this.loadingCampos = false;
      }
    },

    getIcon(magnitudTipo) {
        if (!magnitudTipo) return 'bi bi-speedometer2';
        const lowerMag = magnitudTipo.toLowerCase();
        if (lowerMag.includes('temperatura')) return 'bi bi-thermometer-half';
        if (lowerMag.includes('humedad')) return 'bi bi-droplet-half';
        if (lowerMag.includes('voltaje') || lowerMag.includes('eléctrico')) return 'bi bi-lightning-charge';
        return 'bi bi-activity'; 
    },    

    toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
    handleThemeChange(event) { this.isDark = event.matches; },
    detectarTemaSistema() {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.isDark = true;
      } else {
        this.isDark = false;
      }
    }
  }
};
</script>

<style scoped lang="scss">
@use "sass:color";


.reportes-contenido {
    padding: 30px 40px;
    max-width: 1600px;
    margin: 0 auto;
}

// 1. PANEL DE CONTROL
.control-panel {
    background-color: $WHITE;
    border-radius: 16px;
    padding: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    margin-bottom: 30px;
    border: 1px solid transparent;
}

.control-section {
    display: flex;
    flex-direction: column;
    gap: 15px;
    position: relative;
    
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        color: $GRAY-COLD;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 8px;
        
        i { color: $PRIMARY-PURPLE; font-size: 1.1rem; }
    }
}

// MINI DASHBOARD
.dashboard-mini {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
    
    .mini-card {
        background-color: $WHITE;
        border-radius: 12px;
        padding: 15px 20px;
        display: flex;
        align-items: center;
        gap: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid $LIGHT-BORDER;
        
        .icon-box {
            width: 45px; height: 45px;
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2rem;
            
            &.purple { background: rgba($PRIMARY-PURPLE, 0.1); color: $PRIMARY-PURPLE; }
            &.green { background: rgba($SUCCESS, 0.1); color: $SUCCESS; }
            &.blue { background: rgba($INFO-COLOR, 0.1); color: $INFO-COLOR; }
        }
        
        .info {
            display: flex; flex-direction: column;
            .label { font-size: 0.8rem; color: $GRAY-COLD; font-weight: 600; text-transform: uppercase; }
            .value { font-size: 1.2rem; font-weight: 700; color: $DARK-TEXT; }
        }
    }
}

.mt-2 { margin-top: 1rem; }

// INDICADOR DE SALUD
.health-status {
    margin-top: 10px;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 8px;
    width: fit-content;
    
    &.online { background-color: rgba($SUCCESS, 0.1); color: $SUCCESS; }
    &.offline { background-color: rgba($DANGER, 0.1); color: $DANGER; }
}

// INPUTS Y TOGGLES
.form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    
    label {
        font-size: 0.85rem;
        font-weight: 600;
        color: $DARK-TEXT;
    }
    
    .input-wrapper {
        position: relative;
        display: flex;
        align-items: center;
        
        .input-icon {
            position: absolute;
            left: 12px;
            color: $GRAY-COLD;
            pointer-events: none;
            font-size: 1rem;
        }
        
        .form-control {
            width: 100%;
            padding: 10px 15px 10px 40px; 
            border-radius: 10px;
            border: 1px solid $LIGHT-BORDER;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            background-color: $WHITE;
            appearance: none; 
            color: $DARK-TEXT;
            
            &:focus {
                border-color: $PRIMARY-PURPLE;
                box-shadow: 0 0 0 3px rgba($PRIMARY-PURPLE, 0.1);
                outline: none;
            }
            &:disabled {
                background-color: #f5f5f5;
                cursor: not-allowed;
                opacity: 0.7;
            }
        }
    }
    
    .info-text { color: $SUCCESS; font-size: 0.8rem; margin-top: 4px; i { margin-right: 4px; } }
}

// ESTILOS DEL SWITCH (TOGGLE)
.switch-group {
    .toggle-wrapper {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .switch {
        position: relative;
        display: inline-block;
        width: 46px;
        height: 24px;
        
        input { opacity: 0; width: 0; height: 0; }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: $INACTIVE-COLOR;
            transition: .4s;
            border-radius: 24px;
            
            &:before {
                position: absolute;
                content: "";
                height: 18px;
                width: 18px;
                left: 3px;
                bottom: 3px;
                background-color: white;
                transition: .4s;
                border-radius: 50%;
            }
        }
        
        input:checked + .slider { background-color: $PRIMARY-PURPLE; }
        input:checked + .slider:before { transform: translateX(22px); }
        input:disabled + .slider { background-color: #eee; cursor: not-allowed; opacity: 0.5; }
    }
    
    .switch-label {
        font-size: 0.9rem;
        font-weight: 600;
        color: $GRAY-COLD;
        &.active { color: $PRIMARY-PURPLE; }
    }
}

// BOTÓN EXPORTAR
.btn-exportar-anomalias {
    margin-top: 15px;
    background: transparent;
    border: 1px solid $PRIMARY-PURPLE;
    color: $PRIMARY-PURPLE;
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    
    &:hover { background: rgba($PRIMARY-PURPLE, 0.1); }
}

// STATUS PILL
.status-pill {
    margin-top: 5px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 0;
    
    &.live { color: $SUCCESS; }
    &.history { color: $PRIMARY-PURPLE; }
    &.warning { color: $WARNING; }
}

// 2. VARIABLES PANEL
.variables-panel {
    margin-bottom: 30px;
    
    .panel-header {
        margin-bottom: 15px;
        h4 { font-size: 1.1rem; font-weight: 700; margin: 0; display: flex; align-items: center; gap: 8px; }
        .subtitle { font-size: 0.85rem; color: $GRAY-COLD; }
        i { color: $PRIMARY-PURPLE; }
    }
    
    .variables-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 15px;
    }
    
    .selectable-card {
        background-color: $WHITE;
        border: 1px solid $LIGHT-BORDER;
        border-radius: 12px;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
        
        &:hover { transform: translateY(-2px); border-color: $PRIMARY-PURPLE; }
        
        &.selected {
            background-color: rgba($PRIMARY-PURPLE, 0.08);
            border-color: $PRIMARY-PURPLE;
            
            .card-icon i { color: $PRIMARY-PURPLE; }
            .check-indicator { opacity: 1; transform: scale(1); }
        }
        
        .card-icon {
            width: 32px; height: 32px;
            background-color: rgba($GRAY-COLD, 0.1);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            i { font-size: 1.1rem; color: $GRAY-COLD; transition: color 0.2s; }
        }
        
        .card-info {
            display: flex; flex-direction: column;
            // 🚨 TEXTO MORADO
            .var-name { font-weight: 600; font-size: 0.9rem; color: $PRIMARY-PURPLE; }
            .var-unit { font-size: 0.75rem; color: $GRAY-COLD; }
        }
        
        .check-indicator {
            position: absolute; top: 8px; right: 8px;
            color: $PRIMARY-PURPLE;
            opacity: 0;
            transform: scale(0.5);
            transition: all 0.2s;
        }
    }
}

.charts-grid-realtime {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
    gap: 30px;
}

// ALERTAS
.alert-box {
    padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; font-weight: 500;
    display: flex; align-items: center; justify-content: center; gap: 10px;
    
    &.empty { background-color: rgba($GRAY-COLD, 0.1); color: #555; }
    &.error { background-color: rgba($DANGER, 0.1); color: $DANGER; }
}
.alert-info { background-color: rgba($GRAY-COLD, 0.1); color: $DARK-TEXT; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }

// -----------------------------------
// TEMAS (DARK MODE)
// -----------------------------------
.theme-dark {
    background-color: $DARK-BG-CONTRAST; 
    color: $LIGHT-TEXT;

    .control-panel, .mini-card {
        background-color: $SUBTLE-BG-DARK;
        border-color: rgba($WHITE, 0.05);
    }
    
    .mini-card .info .value { color: $WHITE; }
    
    .form-group label { color: $LIGHT-TEXT; }
    
    .form-control {
        background-color: $DARK-INPUT-BG !important;
        border-color: $DARK-BORDER !important;
        color: $WHITE !important;
        
        &:focus { border-color: $PRIMARY-PURPLE !important; }
        &:disabled { background-color: rgba(0,0,0,0.2) !important; }
    }
    
    .section-title { color: $WHITE; }
    
    .selectable-card {
        background-color: $SUBTLE-BG-DARK;
        border-color: $DARK-BORDER;
        
        .var-name { color: $PRIMARY-PURPLE; } 
        .card-icon { background-color: rgba($WHITE, 0.05); }
        
        &:hover { 
            border-color: $PRIMARY-PURPLE; 
            background-color: color.adjust($SUBTLE-BG-DARK, $lightness: 5%); 
        }
        &.selected { background-color: rgba($PRIMARY-PURPLE, 0.15); }
    }
    
    .alert-box.empty { background-color: rgba($WHITE, 0.05); color: $LIGHT-TEXT; }
    .alert-info { background-color: rgba($WHITE, 0.05); color: $LIGHT-TEXT; }
}

.theme-light {
    background-color: $WHITE-SOFT;
    .control-panel, .mini-card { border-color: $LIGHT-BORDER; }
    .selectable-card { .var-name { color: $PRIMARY-PURPLE; } } 
}
</style>