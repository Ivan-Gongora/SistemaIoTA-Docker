<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma 
        titulo="Reportes y Análisis"
        subtitulo="Exploración histórica de datos IoT"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="reportes-contenido">
        
        <!-- PANEL DE CONTROL UNIFICADO -->
        <div class="control-panel" :class="{ 'theme-dark': isDark }">
            
            <!-- SECCIÓN 1: ORIGEN -->
            <div class="control-section">
                <h4 class="section-title"><i class="bi bi-hdd-network"></i> Origen de Datos</h4>
                
                <div class="form-group">
                    <label>Proyecto</label>
                    <div class="input-wrapper">
                        <i class="bi bi-folder2-open input-icon"></i>
                        <select v-model="proyectoSeleccionadoId" @change="cargarDispositivos" class="form-control">
                            <option :value="null" disabled>
                                {{ loadingProyectos ? 'Cargando...' : 'Seleccionar...' }}
                            </option>
                            <option v-for="p in proyectos" :key="p.id" :value="p.id">{{ p.nombre }}</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>Dispositivo</label>
                    <div class="input-wrapper">
                        <i class="bi bi-cpu input-icon"></i>
                        <select v-model="dispositivoSeleccionadoId" @change="cargarCamposYFechas" class="form-control" :disabled="!proyectoSeleccionadoId">
                            <option :value="null" disabled>
                                {{ loadingDispositivos ? 'Cargando...' : 'Seleccionar...' }}
                            </option>
                            <option v-for="d in dispositivos" :key="d.id" :value="d.id">{{ d.nombre }}</option>
                        </select>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 2: TIEMPO -->
            <div class="control-section time-section">
                <h4 class="section-title"><i class="bi bi-calendar-range"></i> Rango de Tiempo</h4>
                
                <div class="time-row">
                    <div class="form-group flex-grow">
                        <label>Inicio</label>
                        <div class="input-wrapper">
                            <input type="date" class="form-control" v-model="fechaInicioSeleccionada" :min="fechaMinimaDisponible" :max="fechaMaximaDisponible" :disabled="!dispositivoSeleccionadoId">
                        </div>
                    </div>
                    <div class="form-group time-input">
                        <label>Hora</label>
                        <div class="input-wrapper">
                            <input type="time" class="form-control" v-model="horaInicioSeleccionada" :disabled="!dispositivoSeleccionadoId">
                        </div>
                    </div>
                </div>

                <div class="time-row">
                    <div class="form-group flex-grow">
                        <label>Fin</label>
                        <div class="input-wrapper">
                            <input type="date" class="form-control" v-model="fechaFinSeleccionada" :min="fechaMinimaDisponible" :max="fechaMaximaDisponible" :disabled="!dispositivoSeleccionadoId">
                        </div>
                    </div>
                    <div class="form-group time-input">
                        <label>Hora</label>
                        <div class="input-wrapper">
                            <input type="time" class="form-control" v-model="horaFinSeleccionada" :disabled="!dispositivoSeleccionadoId">
                        </div>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 3: CONFIGURACIÓN -->
            <div class="control-section config-section">
                <h4 class="section-title"><i class="bi bi-sliders"></i> Preferencias</h4>
                
                <div class="form-group">
                    <label>Visualización</label>
                    <div class="input-wrapper">
                        <i class="bi bi-graph-up input-icon"></i>
                        <select v-model="modoVista" class="form-control" :disabled="!dispositivoSeleccionadoId">
                            <option value="multiple">Múltiples Gráficos</option>
                            <option value="combinado">Gráfico Combinado</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label>Procesamiento</label>
                    <div class="input-wrapper">
                        <i class="bi bi-database-gear input-icon"></i>
                        <select v-model="metodoCarga" class="form-control" :disabled="!dispositivoSeleccionadoId">
                            <option value="optimizado">Optimizado (Promedios)</option>
                            <option value="puro">Datos Puros (Raw)</option>
                        </select>
                    </div>
                    
                    <!-- Indicador de Estado Elegante -->
                    <div class="status-pill" :class="metodoCarga">
                        <i :class="metodoCarga === 'puro' ? 'bi bi-exclamation-triangle-fill' : 'bi bi-lightning-charge-fill'"></i>
                        <span>{{ metodoCarga === 'puro' ? 'Carga intensiva' : 'Rendimiento óptimo' }}</span>
                    </div>
                    <div class="form-group">
                            <label>Análisis</label>
                            <div class="input-wrapper toggle-wrapper">
                                <label class="switch">
                                    <input type="checkbox" v-model="activarAnalisis" :disabled="!dispositivoSeleccionadoId">
                                    <span class="slider round"></span>
                                </label>
                                <span class="toggle-label">
                                    {{ activarAnalisis ? 'Detección Activa' : 'Desactivado' }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="limits-config" v-if="activarAnalisis">
                        <h5 class="limits-title">Límites de Alerta</h5>
                        
                        <div class="limit-group">
                            <label><i class="bi bi-thermometer-half"></i> Temp (°C)</label>
                            <div class="limit-inputs">
                                <input type="number" v-model.number="limites.tempMin" class="limit-input" placeholder="Min">
                                <span>-</span>
                                <input type="number" v-model.number="limites.tempMax" class="limit-input" placeholder="Max">
                            </div>
                        </div>

                        <div class="limit-group">
                            <label><i class="bi bi-droplet-half"></i> Humedad (%)</label>
                            <div class="limit-inputs">
                                <input type="number" v-model.number="limites.humMin" class="limit-input" placeholder="Min">
                                <span>-</span>
                                <input type="number" v-model.number="limites.humMax" class="limit-input" placeholder="Max">
                            </div>
                        </div>
                    </div>
            </div>
        </div>
        
        <!-- SELECTOR DE VARIABLES (Grid Moderno) -->
        <div class="variables-panel" v-if="campos.length > 0">
            <div class="panel-header">
                <h4><i class="bi bi-check2-square"></i> Variables Disponibles</h4>
                <span class="subtitle">Seleccione las métricas a graficar</span>
            </div>
            
            <div v-if="loadingCampos" class="loading-state">
                <div class="spinner"></div> Cargando variables...
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
                    <div class="check-indicator">
                        <i class="bi bi-check-lg"></i>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- ALERTA DE ESTADO -->
        <div v-if="errorCampos" class="alert-box error">
            <i class="bi bi-x-circle"></i> {{ errorCampos }}
        </div>
        <div v-if="!loadingCampos && dispositivoSeleccionadoId && campos.length === 0" class="alert-box empty">
            <i class="bi bi-inbox"></i> Este dispositivo no tiene variables configuradas.
        </div>
        
        <!-- GRÁFICOS -->
        <div class="charts-container">
            <div class="charts-grid-multiple" v-if="camposFiltrados.length > 0 && modoVista === 'multiple' && dateRange.inicio">
                <GraficoHistorico
                    v-for="campo in camposFiltrados"
                    :key="'sep-'+campo.id"
                    :campo-id="campo.id"
                    :titulo="campo.nombre"
                    :fecha-inicio="dateRange.inicio" 
                    :fecha-fin="dateRange.fin"
                    :is-dark="isDark"
                    :metodo-carga="metodoCarga"
                    :incluir-analisis="activarAnalisis"
                    :limites-personalizados="limites"
                />
            </div>
            
            <div class="charts-grid-single" v-else-if="camposFiltrados.length > 0 && modoVista === 'combinado' && dateRange.inicio">
                <GraficoCombinado
                    :key="'comb-'+dispositivoSeleccionadoId" 
                    :campos="camposFiltrados"
                    :fecha-inicio="dateRange.inicio"
                    :fecha-fin="dateRange.fin"
                    :is-dark="isDark"
                    :metodo-carga="metodoCarga"
                />
            </div>
        </div>
        
      </div>
    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import GraficoHistorico from './GraficoHistorico.vue';
import GraficoCombinado from './GraficoCombinado.vue'; 

export default {
    name: 'VistaReportes',
    components: {
        BarraLateralPlataforma,
        EncabezadoPlataforma,
        GraficoHistorico,
        GraficoCombinado
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

            // Fechas
            fechaMinimaDisponible: null,
            fechaMaximaDisponible: null,
            fechaInicioSeleccionada: null,
            fechaFinSeleccionada: null,
            horaInicioSeleccionada: '00:00',
            horaFinSeleccionada: '23:59',

            modoVista: 'multiple',
            metodoCarga: 'optimizado', 
            
            loadingProyectos: true,
            loadingDispositivos: false,
            loadingCampos: false,
            errorCampos: null,
            error: null,
            activarAnalisis: false,
            limites: {
                tempMin: 20,
                tempMax: 26,
                humMin: 30,
                humMax: 60
            }
        };
    },
    
    computed: {
        dateRange() {
            if (!this.fechaInicioSeleccionada || !this.fechaFinSeleccionada) {
                return { inicio: null, fin: null };
            }
            try {
                const inicioLocal = `${this.fechaInicioSeleccionada}T${this.horaInicioSeleccionada}:00`;
                const finLocal = `${this.fechaFinSeleccionada}T${this.horaFinSeleccionada}:00`;
                return { inicio: inicioLocal, fin: finLocal };
            } catch (e) {
                return { inicio: null, fin: null };
            }
        },
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
    },watch: {
    metodoCarga(nuevoModo) {
        if (nuevoModo === 'puro' && this.camposSeleccionadosIds.length > 2) {
            this.camposSeleccionadosIds = this.camposSeleccionadosIds.slice(0, 2);
            alert("⚠️ Se han reducido las gráficas a 2 por seguridad en modo Datos Puros.");
        }
    }
},
    methods: {
        toggleCampo(id) {
            const index = this.camposSeleccionadosIds.indexOf(id);
            if (index === -1) {
        // Intentando agregar uno nuevo
                if (this.metodoCarga === 'puro' && this.camposSeleccionadosIds.length >= 2) {
                    alert("⚠️ Rendimiento: En modo 'Datos Puros' solo puedes ver máximo 2 gráficas a la vez.");
                    return; 
                }
                this.camposSeleccionadosIds.push(id);
            } else {
                // Quitando uno existente
                this.camposSeleccionadosIds.splice(index, 1);
    }
        },
        // ------------------------------------------------------
        // 1. CARGAR PROYECTOS 
        // ------------------------------------------------------
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

        // ------------------------------------------------------
        // 2. CARGAR DISPOSITIVOS 
        // ------------------------------------------------------
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
                    await this.cargarCamposYFechas();
                }
            } catch (err) {
                console.error(err);
            } finally {
                this.loadingDispositivos = false;
            }
        },
    
        async cargarCamposYFechas() {
            await this.cargarCampos();
            await this.cargarRangoDeFechas();
        },

        // ------------------------------------------------------
        // 3. CARGAR CAMPOS 
        // ------------------------------------------------------
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
                
            } catch (err) {
                console.error("Error al cargar campos:", err);
                this.errorCampos = 'Error al cargar los campos.';
            } finally {
                this.loadingCampos = false;
            }
        },
        
        // ------------------------------------------------------
        // FECHAS E ICONOS
        // ------------------------------------------------------
        async cargarRangoDeFechas() {
            const token = localStorage.getItem('accessToken');
            if (!this.dispositivoSeleccionadoId) return;

            try {
                const response = await fetch(`${API_BASE_URL}/api/valores/rango-fechas-dispositivo/${this.dispositivoSeleccionadoId}`, { 
                    headers: { 'Authorization': `Bearer ${token}` } 
                });
                
                if (response.ok) {
                    const rango = await response.json(); 
                    if (rango.fecha_minima) {
                        this.fechaMinimaDisponible = rango.fecha_minima.split('T')[0];
                        this.fechaInicioSeleccionada = this.fechaMinimaDisponible;
                    }
                    if (rango.fecha_maxima) {
                        this.fechaMaximaDisponible = rango.fecha_maxima.split('T')[0];
                        this.fechaFinSeleccionada = this.fechaMaximaDisponible;
                    }
                }
            } catch (err) {
                const hoy = new Date().toISOString().split('T')[0];
                this.fechaInicioSeleccionada = hoy;
                this.fechaFinSeleccionada = hoy;
            }
        },
        
        getIcon(magnitudTipo) {
            if (!magnitudTipo) return 'bi bi-speedometer2';
            const lower = magnitudTipo.toLowerCase();
            if (lower.includes('temperatura')) return 'bi bi-thermometer-half';
            if (lower.includes('humedad')) return 'bi bi-droplet-half';
            if (lower.includes('voltaje')) return 'bi bi-lightning-charge';
            return 'bi bi-activity'; 
        },
            
        toggleSidebar() { this.isSidebarOpen = !this.isSidebarOpen; },
        handleThemeChange(event) { this.isDark = event.matches; },
        detectarTemaSistema() {
            this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
    }
};
</script>

<style scoped lang="scss">
@use "sass:color";

// =============================================================================
// 1. LAYOUT PRINCIPAL & RESPONSIVIDAD
// =============================================================================
.reportes-contenido {
    padding: 30px 40px;
    max-width: 1600px;
    margin: 0 auto;
    transition: all 0.3s ease;

    @media (max-width: 768px) {
        padding: 15px 20px;
    }
}

// -----------------------------------
// 2. PANEL DE CONTROL (GRID)
// -----------------------------------
.control-panel {
    border-radius: 16px; 
    padding: 25px;
    box-shadow: $shadow-soft; 
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 30px;
    margin-bottom: 30px;
    border: 1px solid transparent;
    transition: background-color 0.3s ease, border-color 0.3s ease;

    @media (max-width: 768px) {
        grid-template-columns: 1fr; 
        gap: 20px;
        padding: 20px;
    }
}

.control-section {
    display: flex;
    flex-direction: column;
    gap: 15px;
    
    .section-title {
        font-size: 0.95rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 8px;
        
        i { font-size: 1.1rem; color: $PRIMARY-PURPLE; }
    }
}

// -----------------------------------
// 3. ELEMENTOS DE FORMULARIO
// -----------------------------------
.form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    
    label {
        font-size: 0.85rem;
        font-weight: 600;
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
            z-index: 2;
        }
        
        .form-control {
            width: 100%;
            padding: 10px 15px 10px 40px; 
            border-radius: 10px;
            border: 1px solid transparent; 
            font-size: 0.95rem;
            transition: all 0.2s ease;
            appearance: none; 
            
            &:focus {
                border-color: $PRIMARY-PURPLE !important;
                box-shadow: 0 0 0 3px rgba($PRIMARY-PURPLE, 0.1);
                outline: none;
            }
            
            &:disabled {
                cursor: not-allowed;
                opacity: 0.7;
            }
        }
    }
}

.time-row {
    display: flex;
    gap: 10px;
    flex-wrap: wrap; 

    .flex-grow { flex: 1; min-width: 140px; }
    .time-input { width: 110px; flex-shrink: 0; }
}

.status-pill {
    margin-top: 5px;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 0;
    
    &.optimizado { color: $SUCCESS; }
    &.puro { color: $WARNING; } 
}

// -----------------------------------
// 4. SECCIÓN DE LÍMITES (NUEVO)
// -----------------------------------
.limits-config {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid; 
    animation: fadeIn 0.3s ease-in-out;

    .limits-title {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 12px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        opacity: 0.8;
    }

    .limit-group {
        margin-bottom: 15px;

        label {
            display: block;
            font-size: 0.85rem;
            font-weight: 500;
            color: $GRAY-COLD;
            margin-bottom: 6px;
            
            i { margin-right: 6px; color: $PRIMARY-PURPLE; }
        }

        .limit-inputs {
            display: flex;
            align-items: center;
            gap: 10px;

            span { color: $GRAY-COLD; font-weight: bold; }

            .limit-input {
                width: 100%;
                padding: 8px 12px;
                font-size: 0.9rem;
                border-radius: 6px; 
                border: 1px solid; 
                transition: all 0.2s ease;
                box-shadow: $box-shadow-sm; 

                &:focus {
                    outline: none;
                    border-color: $PRIMARY-PURPLE !important;
                    box-shadow: 0 0 0 3px rgba($PRIMARY-PURPLE, 0.15);
                }
                
                &::-webkit-inner-spin-button, &::-webkit-outer-spin-button { 
                    -webkit-appearance: none; margin: 0; 
                }
            }
        }
    }
}

// Switch iOS Style
.toggle-wrapper { display: flex; align-items: center; gap: 10px; }
.toggle-label { font-size: 0.85rem; font-weight: 500; color: $GRAY-COLD; }

.switch {
    position: relative;
    display: inline-block;
    width: 44px; 
    height: 24px;
    
    input { opacity: 0; width: 0; height: 0; }
    
    .slider {
        position: absolute;
        cursor: pointer;
        top: 0; left: 0; right: 0; bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 34px;
        
        &:before {
            position: absolute;
            content: "";
            height: 18px; width: 18px;
            left: 3px; bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
    }
    
    input:checked + .slider { background-color: $PRIMARY-PURPLE; }
    input:checked + .slider:before { transform: translateX(20px); }
}

// -----------------------------------
// 5. GRID DE VARIABLES
// -----------------------------------
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
        border: 1px solid; 
        border-radius: 12px;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
        
        &:hover { transform: translateY(-2px); border-color: $PRIMARY-PURPLE !important; }
        
        &.selected {
            background-color: rgba($PRIMARY-PURPLE, 0.08) !important;
            border-color: $PRIMARY-PURPLE !important;
            
            .card-icon i { color: $PRIMARY-PURPLE; }
            .check-indicator { opacity: 1; transform: scale(1); }
        }
        
        .card-icon {
            width: 32px; height: 32px;
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            i { font-size: 1.1rem; transition: color 0.2s; }
        }
        
        .card-info {
            display: flex; flex-direction: column;
            .var-name { font-weight: 600; font-size: 0.9rem; }
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

// -----------------------------------
// 6. GRÁFICOS Y ALERTAS
// -----------------------------------
.charts-container { margin-top: 30px; }

.charts-grid-multiple { 
    display: grid; 
    gap: 25px;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr)); 
    @media (max-width: 768px) { grid-template-columns: 1fr; }
}

.charts-grid-single { 
    display: grid; 
    gap: 25px; 
    grid-template-columns: 1fr; 
}

.alert-box {
    padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; font-weight: 500;
    display: flex; align-items: center; justify-content: center; gap: 10px;
    
    &.empty { background-color: rgba($GRAY-COLD, 0.1); color: #555; }
    &.error { background-color: rgba($DANGER, 0.1); color: $DANGER; }
}

// =============================================================================
// 7. DEFINICIÓN DE TEMAS (CLARO / OSCURO)
// =============================================================================

// --- TEMA CLARO ---
.theme-light {
    background-color: $WHITE-SOFT;
    
    .control-panel {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
    }

    .form-group label { color: $DARK-TEXT; }

    .form-control {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
        color: $DARK-TEXT;
        &:disabled { background-color: #f5f5f5; }
    }

    .section-title { color: $GRAY-COLD; }

    .limits-config {
        border-top-color: $LIGHT-BORDER;
        .limits-title { color: $DARK-TEXT; }
        .limit-input {
            background-color: $WHITE;
            border-color: $LIGHT-BORDER;
            color: $DARK-TEXT;
            &::placeholder { color: rgba($GRAY-COLD, 0.6); }
        }
    }

    .selectable-card {
        background-color: $WHITE;
        border-color: $LIGHT-BORDER;
        .card-icon { background-color: rgba($GRAY-COLD, 0.1); i { color: $GRAY-COLD; } }
        .var-name { color: $BLACK; }
    }
}

// --- TEMA OSCURO ---
.theme-dark {
    background-color: $DARK-BG-CONTRAST; // Fondo principal oscuro
    color: $LIGHT-TEXT;

    .control-panel {
        background-color: $SUBTLE-BG-DARK; // Tarjeta oscura
        border-color: rgba($WHITE, 0.05);
        box-shadow: $shadow-dark;
    }
    
    .form-group label { color: $GRAY-LIGHT; }
    
    .form-control {
        background-color: $DARK-INPUT-BG !important;
        border-color: $DARK-BORDER !important;
        color: $WHITE !important;
        
        &:disabled { background-color: rgba(0,0,0,0.2) !important; color: $GRAY-COLD !important; }
        
        &:-webkit-autofill {
            -webkit-box-shadow: 0 0 0 30px $DARK-INPUT-BG inset !important;
            -webkit-text-fill-color: $WHITE !important;
        }
    }
    
    .section-title { color: $WHITE; }
    
    // Configuración de límites en oscuro
    .limits-config {
        border-top-color: $DARK-BORDER;
        .limits-title { color: $LIGHT-TEXT; }
        
        .limit-input {
            background-color: $DARK-INPUT-BG;
            border-color: $DARK-BORDER;
            color: $LIGHT-TEXT;
            box-shadow: none; 
            
            // 🟢 SOLUCIÓN: Usar color.adjust en lugar de lighten
            &:focus { 
                border-color: $PRIMARY-PURPLE;
                background-color: color.adjust($DARK-INPUT-BG, $lightness: 5%); 
            }
        }
    }
    
    .selectable-card {
        background-color: $SUBTLE-BG-DARK;
        border-color: $DARK-BORDER;
        
        .var-name { color: $WHITE; }
        .card-icon { background-color: rgba($WHITE, 0.05); i { color: $GRAY-COLD; } }
        
        &:hover { 
            // 🟢 SOLUCIÓN: Usar color.adjust
            background-color: color.adjust($SUBTLE-BG-DARK, $lightness: 5%); 
        }
    }
    
    .alert-box.empty { background-color: rgba($WHITE, 0.05); color: $GRAY-LIGHT; }
}

// Animación Global
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>