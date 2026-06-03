<template>
  <div class="plataforma_layout" :class="{ 'theme_dark': isDark, 'theme_light': !isDark }">
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma_contenido" :class="{ 'shifted': isSidebarOpen }">
      <EncabezadoPlataforma 
        titulo="Reportes Históricos"
        subtitulo="Exploración temporal de telemetría IoT"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="reportes_wrapper">
        <div class="header_dashboard">
          <div class="header_titles">
            <h2 class="main_title">Historial de Telemetría</h2>
            <span class="sub_title">Monitoreo de datos IoT</span>
          </div>
          
          <div class="header_selectors">
            <div class="input_compact">
              <i class="bi bi-folder2-open icon_purple"></i>
              <select v-model="form.proyectoId" @change="cambiarProyecto" class="select_invisible">
                <option :value="null" disabled>{{ loadingProyectos ? 'Cargando...' : 'Proyecto' }}</option>
                <option v-for="p in proyectos" :key="p.id" :value="p.id">{{ p.nombre }}</option>
              </select>
            </div>
            <div class="input_compact">
              <i class="bi bi-cpu icon_purple"></i>
              <select v-model="form.dispositivoId" @change="cambiarDispositivo" class="select_invisible" :disabled="!form.proyectoId">
                <option :value="null" disabled>{{ loadingDispositivos ? 'Cargando...' : 'Dispositivo' }}</option>
                <option v-for="d in dispositivos" :key="d.id" :value="d.id">{{ d.nombre }}</option>
              </select>
            </div>
          </div>
        </div>

        <div class="config_toolbar shadow_soft">
          <div class="toolbar_top">
            
            <div class="date_group">
              <div class="date_input">
                <i class="bi bi-calendar-event text_muted"></i>
                <input type="date" v-model="form.fechaInicio" :min="fechaMinima" :max="form.fechaFin" :disabled="!form.dispositivoId">
              </div>
              <span class="text_muted fw_bold">hasta</span>
              <div class="date_input">
                <i class="bi bi-calendar-check text_muted"></i>
                <input type="date" v-model="form.fechaFin" :min="form.fechaInicio" :max="fechaMaxima" :disabled="!form.dispositivoId">
              </div>
            </div>

            <div class="view_toggles">
               <button class="pill_btn" :class="{ 'activo': form.modoVista === 'multiple' }" @click="form.modoVista = 'multiple'">Múltiple</button>
               <button class="pill_btn" :class="{ 'activo': form.modoVista === 'combinado' }" @click="form.modoVista = 'combinado'">Combinado</button>
               <div class="divider"></div>
               <button class="pill_btn optimizado" :class="{ 'activo': form.metodoCarga === 'optimizado' }" @click="form.metodoCarga = 'optimizado'">Optimizado</button>
               <button class="pill_btn puro" :class="{ 'activo': form.metodoCarga === 'puro' }" @click="form.metodoCarga = 'puro'">Raw</button>
            </div>

            <div class="action_group">
              <label class="switch_wrapper" title="Evaluar datos de la base de datos">
                <span class="fw_bold text_muted me-2">Límites ASHRAE</span>
                <div class="switch">
                  <input type="checkbox" v-model="form.activarAnalisis" :disabled="!form.dispositivoId">
                  <span class="slider round"></span>
                </div>
              </label>
              <button @click="aplicarFiltros" class="btn_extract" :disabled="!listoParaConsultar">
                <i class="bi bi-cloud-arrow-down-fill me-2"></i> Extraer Datos
              </button>
            </div>
            
          </div>

          <div class="limits_panel" v-if="form.activarAnalisis">
            <span class="limits_title"><i class="bi bi-sliders"></i> Ajuste de Umbrales</span>
            <div class="limit_box">
              <label>Temp Mín (°C)</label>
              <input type="number" v-model.number="form.limites.tempMin" class="limit_input">
            </div>
            <div class="limit_box">
              <label>Temp Máx (°C)</label>
              <input type="number" v-model.number="form.limites.tempMax" class="limit_input">
            </div>
            <div class="limit_box">
              <label>Hum Mín (%)</label>
              <input type="number" v-model.number="form.limites.humMin" class="limit_input">
            </div>
            <div class="limit_box">
              <label>Hum Máx (%)</label>
              <input type="number" v-model.number="form.limites.humMax" class="limit_input">
            </div>
          </div>

          <div class="metrics_bar mt-3" v-if="campos.length > 0">
            <span class="fw_bold text_muted me-3 mt-1">Variables:</span>
            <div class="metrics_scroll">
              <div 
                v-for="c in campos" 
                :key="c.id" 
                class="metric_chip"
                :class="{ 'activo': form.camposIds.includes(c.id) }"
                @click="toggleCampo(c.id)"
              >
                <i :class="getIcon(c.nombre)"></i>
                <span class="m_name">{{ c.nombre }}</span>
                <span class="m_unit">{{ c.unidad?.simbolo || c.simbolo_unidad || '' }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="errorMsg" class="alert_box error shadow_soft">
          <i class="bi bi-exclamation-triangle-fill"></i> {{ errorMsg }}
        </div>

        <div class="zona_datos mt-4" v-if="filtrosAplicados.listos">
          
          <div class="kpi_summary_grid mb-4" v-if="Object.keys(kpis).length > 0">
            <div class="kpi_card" v-for="(kpi, id) in kpis" :key="id">
              <div class="kpi_header">
                <div class="icon_wrap" :class="kpi.claseColor">
                  <i :class="getIcon(kpi.nombre)"></i>
                </div>
                <span class="kpi_title">{{ kpi.nombre }}</span>
              </div>
              
              <div class="kpi_body">
                <template v-if="kpi.es_texto">
                   <div v-for="(txt, i) in kpi.top_textos" :key="i" class="text_muted small fw_bold text-truncate" :title="txt.texto">
                      <span class="text-primary">{{ txt.conteo }}x</span> {{ txt.texto }}
                   </div>
                   <span class="d-block text_muted small fw_bold mt-1">INCIDENCIAS PRINCIPALES</span>
                </template>
                <template v-else>
                   <div class="d-flex align-items-baseline gap-1">
                     <span class="kpi_value" :class="kpi.claseColor">{{ kpi.avg !== null ? kpi.avg : '-' }}</span>
                     <span class="kpi_unit">{{ kpi.unidad }}</span>
                   </div>
                   <span class="d-block text_muted small fw_bold mt-1">PROMEDIO</span>
                </template>
              </div>

              <div class="kpi_footer border-top pt-2 mt-2">
                <div class="kpi_minmax" v-if="!kpi.es_texto">
                  <span class="text_muted small"><i class="bi bi-arrow-down-short text-info"></i> Mín: <strong>{{ kpi.min !== null ? kpi.min : '-' }}</strong></span>
                  <span class="text_muted small"><i class="bi bi-arrow-up-short text-danger"></i> Máx: <strong>{{ kpi.max !== null ? kpi.max : '-' }}</strong></span>
                </div>
                <div class="kpi_minmax" v-else>
                  <span class="text_muted small">Frecuencia de Registros</span>
                </div>
              </div>
            </div>
          </div>

          <div class="charts_grid_multiple" v-if="filtrosAplicados.modoVista === 'multiple'">
            <GraficoTemperatura
              v-if="tieneTemperatura"
              :campos="obtenerObjetosCamposFiltrados('temperatura')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :limites="filtrosAplicados.limites"
              :metodo-carga="filtrosAplicados.metodoCarga"
              @estadisticas="registrarKpi"
            />

            <GraficoHumedad
              v-if="tieneHumedad"
              :campos="obtenerObjetosCamposFiltrados('humedad')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :limites="filtrosAplicados.limites"
              :metodo-carga="filtrosAplicados.metodoCarga"
              @estadisticas="registrarKpi"
            />

            <GraficoElectrico
              v-if="tieneElectrico"
              :campos="obtenerObjetosCamposFiltrados('potencia', 'corriente')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
              @estadisticas="registrarKpi"
            />

            <GraficoEnergia
              v-if="tieneEnergia"
              :campos="obtenerObjetosCamposFiltrados('energia', 'kwh')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
              @estadisticas="registrarKpi"
            />

            <GraficoIluminacion
              v-if="tieneIluminacion"
              :campos="obtenerObjetosCamposFiltrados('iluminacion', 'luz')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
              @estadisticas="registrarKpi"
            />

            <GraficoMovimiento
              v-if="tieneMovimiento"
              :campos="obtenerObjetosCamposFiltrados('movimiento', 'presencia')"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
              @estadisticas="registrarKpi"
            />

            <GraficoHistorico
              v-for="campoId in camposGenericos"
              :key="`hist-${campoId}`"
              :campo-id="campoId"
              :titulo="obtenerNombreCampo(campoId)"
              :fecha-inicio="filtrosAplicados.rangoInicio" 
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
              :incluir-analisis="filtrosAplicados.activarAnalisis"
              :limites-personalizados="filtrosAplicados.limites"
              @estadisticas="registrarKpi"
            />
          </div>
          
          <div class="charts_grid_single" v-else>
            <GraficoCombinado
              :key="`comb-${filtrosAplicados.rangoInicio}`"
              :campos="obtenerObjetosCampos(filtrosAplicados.camposIds)"
              :fecha-inicio="filtrosAplicados.rangoInicio"
              :fecha-fin="filtrosAplicados.rangoFin"
              :is-dark="isDark"
              :metodo-carga="filtrosAplicados.metodoCarga"
            />
          </div>
        </div>

        <div v-if="!filtrosAplicados.listos && !loadingProyectos" class="empty_state glass_panel mt-4 text-center py-5 shadow_soft">
          <div class="empty_icon"><i class="bi bi-layers-fill"></i></div>
          <h4 class="fw_bold mt-3 text_light">Panel de Telemetría</h4>
          <p class="text_muted">Configura el dispositivo, selecciona fechas y extrae los datos.</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import GraficoCombinado from './GraficoCombinado.vue';
import GraficoTemperatura from './GraficoTemperatura.vue';
import GraficoHumedad from './GraficoHumedad.vue';
import GraficoElectrico from './GraficoElectrico.vue';
import GraficoEnergia from './GraficoEnergia.vue';
import GraficoIluminacion from './GraficoIluminacion.vue';
import GraficoMovimiento from './GraficoMovimiento.vue';
import GraficoHistorico from './GraficoHistorico.vue';

export default {
  name: 'VistaReportesHistoricos',
  components: {
    BarraLateralPlataforma,
    EncabezadoPlataforma,
    GraficoCombinado,
    GraficoTemperatura,
    GraficoHumedad,
    GraficoElectrico,
    GraficoEnergia,
    GraficoIluminacion,
    GraficoMovimiento,
    GraficoHistorico
  },
  data() {
    return {
      isDark: true,
      isSidebarOpen: true,
      proyectos: [],
      dispositivos: [],
      campos: [],
      kpis: {},
      loadingProyectos: true,
      loadingDispositivos: false,
      loadingCampos: false,
      errorMsg: null,
      fechaMinima: null,
      fechaMaxima: null,
      abortControllers: {},
      form: {
        proyectoId: null,
        dispositivoId: null,
        fechaInicio: '',
        fechaFin: '',
        horaInicio: '00:00',
        horaFin: '23:59',
        camposIds: [],
        modoVista: 'multiple',
        metodoCarga: 'optimizado',
        activarAnalisis: false,
        limites: {
          tempMin: 20,
          tempMax: 26,
          humMin: 30,
          humMax: 65
        }
      },
      filtrosAplicados: {
        listos: false,
        dispositivoId: null,
        camposIds: [],
        rangoInicio: '',
        rangoFin: '',
        modoVista: 'multiple',
        metodoCarga: 'optimizado',
        activarAnalisis: false,
        limites: {}
      }
    };
  },
  computed: {
    tieneTemperatura() { return this.verificarSeleccion('temperatura'); },
    tieneHumedad() { return this.verificarSeleccion('humedad'); },
    tieneElectrico() { return this.verificarSeleccion('potencia', 'corriente'); },
    tieneEnergia() { return this.verificarSeleccion('energia', 'kwh'); },
    tieneIluminacion() { return this.verificarSeleccion('iluminacion', 'luz'); },
    tieneMovimiento() { return this.verificarSeleccion('movimiento', 'presencia'); },
    camposGenericos() {
      return this.filtrosAplicados.camposIds.filter(id => {
        const nombre = this.obtenerNombreCampo(id).toLowerCase();
        const esTermo = nombre.includes('temperatura') || nombre.includes('humedad');
        const esElec = nombre.includes('potencia') || nombre.includes('corriente');
        const esEne = nombre.includes('energia') || nombre.includes('kwh');
        const esIlu = nombre.includes('iluminacion') || nombre.includes('luz');
        const esMov = nombre.includes('movimiento') || nombre.includes('presencia');
        return !esTermo && !esElec && !esEne && !esIlu && !esMov;
      });
    },
    listoParaConsultar() {
      return this.form.dispositivoId && 
             this.form.fechaInicio && 
             this.form.fechaFin && 
             this.form.camposIds.length > 0;
    }
  },
  watch: {
    'form.metodoCarga'(nuevoModo) {
      if (nuevoModo === 'puro' && this.form.camposIds.length > 1) {
        this.form.camposIds = this.form.camposIds.slice(0, 1);
        this.errorMsg = "Modo Raw activo. Restringimos la selección a UNA métrica para proteger la memoria de TU navegador.";
        setTimeout(() => { this.errorMsg = null; }, 5000);
      }
    }
  },
  mounted() {
    this.detectarTema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleTheme);
    }
    this.cargarProyectos();
  },
  beforeUnmount() {
    this.limpiarTodasLasConsultas();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleTheme);
    }
  },
  methods: {
    abortarPeticion(clave) {
      if (this.abortControllers[clave]) {
        this.abortControllers[clave].abort();
      }
      this.abortControllers[clave] = new AbortController();
      return this.abortControllers[clave].signal;
    },
    limpiarTodasLasConsultas() {
      Object.values(this.abortControllers).forEach(ac => ac.abort());
      this.filtrosAplicados.listos = false;
    },
    async cambiarProyecto() {
      this.limpiarTodasLasConsultas();
      this.dispositivos = [];
      this.form.dispositivoId = null;
      await this.cargarDispositivos();
    },
    async cambiarDispositivo() {
      this.limpiarTodasLasConsultas();
      await this.cargarCamposYFechas();
    },
    detectarTema() {
      this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    },
    handleTheme(e) {
      this.isDark = e.matches;
    },
    toggleSidebar() {
      this.isSidebarOpen = !this.isSidebarOpen;
    },
    registrarKpi(datosKpi) {
      this.kpis[datosKpi.id] = datosKpi;
    },
    getIcon(tipo) {
      if (!tipo) return 'bi bi-activity';
      const t = tipo.toLowerCase();
      if (t.includes('temperatura')) return 'bi bi-thermometer-half';
      if (t.includes('humedad')) return 'bi bi-droplet-half';
      if (t.includes('potencia') || t.includes('energia') || t.includes('kwh')) return 'bi bi-lightning-charge-fill';
      if (t.includes('corriente')) return 'bi bi-plug-fill';
      if (t.includes('luz') || t.includes('iluminacion')) return 'bi bi-brightness-high-fill';
      if (t.includes('movimiento')) return 'bi bi-person-walking';
      return 'bi bi-graph-up';
    },
    toggleCampo(id) {
      const idx = this.form.camposIds.indexOf(id);
      if (idx === -1) {
        if (this.form.metodoCarga === 'puro' && this.form.camposIds.length >= 1) {
          this.errorMsg = "Modo Raw activo. Extraes una métrica a la vez.";
          setTimeout(() => { this.errorMsg = null; }, 3000);
          return;
        }
        this.form.camposIds.push(id);
      } else {
        this.form.camposIds.splice(idx, 1);
      }
    },
    obtenerNombreCampo(id) {
      const c = this.campos.find(x => x.id === id);
      return c ? c.nombre : 'Variable Desconocida';
    },
    obtenerObjetosCampos(ids) {
      return this.campos.filter(c => ids.includes(c.id));
    },
    verificarSeleccion(...palabrasClave) {
      return this.filtrosAplicados.camposIds.some(id => {
        const nombre = this.obtenerNombreCampo(id).toLowerCase();
        return palabrasClave.some(p => nombre.includes(p));
      });
    },
    obtenerObjetosCamposFiltrados(...palabrasClave) {
      const idsValidos = this.filtrosAplicados.camposIds.filter(id => {
        const nombre = this.obtenerNombreCampo(id).toLowerCase();
        return palabrasClave.some(p => nombre.includes(p));
      });
      return this.obtenerObjetosCampos(idsValidos);
    },

    async cargarProyectos() {
      const signal = this.abortarPeticion('proyectos');
      this.loadingProyectos = true;
      const token = localStorage.getItem('accessToken');
      const resultadoLocal = JSON.parse(localStorage.getItem('resultado') || '{}');
      const usuarioId = resultadoLocal.usuario?.id;

      if (!token || !usuarioId) return; 

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/proyectos/usuario/${usuarioId}?page=1&limit=100`, { 
          headers: { 'Authorization': `Bearer ${token}` },
          signal 
        });
        
        if (response.ok) {
          const res = await response.json();
          this.proyectos = res.data || [];
          if (this.proyectos.length > 0) {
            this.form.proyectoId = this.proyectos[0].id;
            await this.cargarDispositivos(); 
          }
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        this.errorMsg = "Problema de red al ubicar proyectos.";
      } finally {
        if (!signal.aborted) this.loadingProyectos = false;
      }
    },

    async cargarDispositivos() {
      const signal = this.abortarPeticion('dispositivos');
      this.loadingDispositivos = true;
      
      const token = localStorage.getItem('accessToken');
      if (!this.form.proyectoId) return;

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/dispositivos/proyecto/${this.form.proyectoId}?page=1&limit=100`, { 
          headers: { 'Authorization': `Bearer ${token}` },
          signal
        });
        
        if (response.ok) { 
          const res = await response.json();
          this.dispositivos = res.data || [];
          if (this.dispositivos.length > 0) {
            this.form.dispositivoId = this.dispositivos[0].id;
            await this.cargarCamposYFechas();
          }
        }
      } catch (err) {
        if (err.name === 'AbortError') return;
        this.errorMsg = "Error al descargar equipos.";
      } finally {
        if (!signal.aborted) this.loadingDispositivos = false;
      }
    },

    async cargarCamposYFechas() {
      this.limpiarFormularioCampos();
      await this.cargarCampos();
      await this.cargarRangoDeFechas();
    },

    limpiarFormularioCampos() {
      this.campos = [];
      this.form.camposIds = [];
      this.fechaMinima = null;
      this.fechaMaxima = null;
      this.form.fechaInicio = '';
      this.form.fechaFin = '';
    },

    async cargarCampos() {
      const signal = this.abortarPeticion('campos');
      this.loadingCampos = true;
      this.errorMsg = null;
      const token = localStorage.getItem('accessToken');
      if (!this.form.dispositivoId) return;

      try {
        const sensoresResponse = await fetch(`${window.API_BASE_URL}/api/sensores/dispositivo/${this.form.dispositivoId}?page=1&limit=50`, { 
          headers: { 'Authorization': `Bearer ${token}` },
          signal
        });
        
        let sensores = [];
        if (sensoresResponse.ok) {
          const res = await sensoresResponse.json();
          sensores = Array.isArray(res) ? res : (res.data || []);
        }

        let todosLosCampos = [];
        for (const sensor of sensores) {
          const camposResponse = await fetch(`${window.API_BASE_URL}/api/sensores/${sensor.id}/campos`, { 
            headers: { 'Authorization': `Bearer ${token}` },
            signal
          });
          
          if (camposResponse.ok) {
            const res = await camposResponse.json();
            const listaCampos = res.campos || (Array.isArray(res) ? res : []);
            todosLosCampos.push(...listaCampos); 
          }
        }
        this.campos = todosLosCampos; 
        
        if (this.campos.length > 0) {
            this.form.camposIds = this.campos.map(c => c.id);
        }

      } catch (err) {
        if (err.name === 'AbortError') return;
        this.errorMsg = 'Fallo al descargar métricas del equipo.';
      } finally {
        if (!signal.aborted) this.loadingCampos = false;
      }
    },

    async cargarRangoDeFechas() {
      const signal = this.abortarPeticion('fechas');
      const token = localStorage.getItem('accessToken');
      if (!this.form.dispositivoId) return;

      try {
        const response = await fetch(`${window.API_BASE_URL}/api/valores/rango-fechas-dispositivo/${this.form.dispositivoId}`, { 
          headers: { 'Authorization': `Bearer ${token}` },
          signal
        });
        
        if (response.ok) {
          const rango = await response.json(); 
          if (rango.fecha_minima && rango.fecha_maxima) {
            this.fechaMinima = rango.fecha_minima.split('T')[0];
            this.fechaMaxima = rango.fecha_maxima.split('T')[0];
            
            this.form.fechaInicio = this.fechaMinima;
            this.form.fechaFin = this.fechaMaxima;
            return;
          }
        }
        this.asignarFechasLocales();
      } catch (err) {
        if (err.name === 'AbortError') return;
        this.asignarFechasLocales();
      }
    },

    asignarFechasLocales() {
      const hoyStr = new Date().toISOString().split('T')[0];
      this.form.fechaInicio = hoyStr;
      this.form.fechaFin = hoyStr;
    },

    aplicarFiltros() {
      this.limpiarTodasLasConsultas();
      this.kpis = {};
      this.filtrosAplicados.dispositivoId = this.form.dispositivoId;
      this.filtrosAplicados.camposIds = [...this.form.camposIds];
      this.filtrosAplicados.rangoInicio = `${this.form.fechaInicio}T${this.form.horaInicio}:00`;
      this.filtrosAplicados.rangoFin = `${this.form.fechaFin}T${this.form.horaFin}:00`;
      this.filtrosAplicados.modoVista = this.form.modoVista;
      this.filtrosAplicados.metodoCarga = this.form.metodoCarga;
      this.filtrosAplicados.activarAnalisis = this.form.activarAnalisis;
      this.filtrosAplicados.limites = { ...this.form.limites };
      
      this.$nextTick(() => {
        this.filtrosAplicados.listos = true;
      });
    }
  }
};
</script>

<style scoped lang="scss">
$WHITE: #FFFFFF;
$WHITE-SOFT: #F7F9FC;
$SUBTLE-BG-LIGHT: #FFFFFF;
$DARK-BG-CONTRAST: #1E1E30;
$SUBTLE-BG-DARK: #2B2B40;

$LIGHT-TEXT: #E4E6EB;
$DARK-TEXT: #333333;
$GRAY-COLD: #99A2AD;
$GRAY-LIGHT: #E0E0E0; 

$DANGER-COLOR: #E74C3C;
$SUCCESS-COLOR: #1ABC9C;
$WARNING-COLOR: #FFC107; 
$PRIMARY-PURPLE: #8A2BE2;
$GRADIENT: linear-gradient(to right, #6F00FF, #A300FF);
$INACTIVE-COLOR: #7F8C8D; 

$DARK-BORDER: #44475A; 
$LIGHT-BORDER: #E0E0E0; 
$DARK-INPUT-BG: #3C3C55; 

$shadow-soft: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
$shadow-dark: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
$shadow-purple: 0 4px 12px rgba(138, 43, 226, 0.35);

$WIDTH-SIDEBAR: 280px; 
$WIDTH-CLOSED: 80px;
$border-radius-lg: 12px; 

.plataforma_layout { display: flex; width: 100%; min-height: 100vh; transition: background-color 0.3s; }
.theme_light { background-color: $WHITE-SOFT; color: $DARK-TEXT; }
.theme_dark { background-color: $DARK-BG-CONTRAST; color: $LIGHT-TEXT; }

.plataforma_contenido { flex-grow: 1; padding: 24px; margin-left: $WIDTH-CLOSED; transition: margin-left 0.3s; }
.shifted { margin-left: $WIDTH-SIDEBAR; }
.reportes_wrapper { max-width: 1600px; margin: 0 auto; }

.header_dashboard { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 20px; }
.main_title { font-size: 1.8rem; font-weight: 800; margin: 0; }
.theme_dark .main_title { color: $WHITE; }
.theme_light .main_title { color: $DARK-TEXT; }
.sub_title { color: $GRAY-COLD; font-size: 0.9rem; }

.header_selectors { display: flex; gap: 12px; }
.input_compact { display: flex; align-items: center; padding: 8px 16px; border-radius: $border-radius-lg; gap: 10px; transition: all 0.2s; }
.theme_light .input_compact { background: $WHITE; border: 1px solid $LIGHT-BORDER; box-shadow: $shadow-soft; }
.theme_dark .input_compact { background: $SUBTLE-BG-DARK; border: 1px solid $DARK-BORDER; box-shadow: $shadow-dark; }
.input_compact:focus-within { border-color: $PRIMARY-PURPLE; box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.3); }

.icon_purple { color: $PRIMARY-PURPLE; font-size: 1.1rem; }
.select_invisible { border: none; background: transparent; font-weight: 700; outline: none; font-size: 0.9rem; width: 160px; }
.theme_light .select_invisible { color: $DARK-TEXT; }
.theme_dark .select_invisible { color: $LIGHT-TEXT; }
.theme_dark .select_invisible option { background: $DARK-BG-CONTRAST; color: $LIGHT-TEXT; }

.config_toolbar { border-radius: $border-radius-lg; padding: 16px 20px; margin-bottom: 20px; }
.theme_light .config_toolbar { background: $WHITE; border: 1px solid $LIGHT-BORDER; }
.theme_dark .config_toolbar { background: $SUBTLE-BG-DARK; border: 1px solid $DARK-BORDER; }

.toolbar_top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }

.date_group { display: flex; align-items: center; gap: 12px; }
.date_input { display: flex; align-items: center; padding: 8px 14px; border-radius: 10px; gap: 8px; }
.theme_light .date_input { background: $WHITE-SOFT; border: 1px solid $LIGHT-BORDER; }
.theme_dark .date_input { background: $DARK-INPUT-BG; border: 1px solid rgba(255, 255, 255, 0.05); }
.date_input input { border: none; background: transparent; outline: none; color: inherit; font-weight: 600; font-size: 0.9rem; }
.theme_dark .date_input input { color: $WHITE; color-scheme: dark; }

.view_toggles { display: flex; align-items: center; gap: 8px; padding: 4px; border-radius: 12px; }
.theme_light .view_toggles { background: $WHITE-SOFT; border: 1px solid $LIGHT-BORDER; }
.theme_dark .view_toggles { background: rgba(0,0,0,0.2); border: 1px solid rgba(255, 255, 255, 0.05); }

.divider { width: 1px; height: 20px; background: $GRAY-COLD; opacity: 0.3; margin: 0 4px; }

.pill_btn { border: none; background: transparent; padding: 6px 14px; border-radius: 8px; font-size: 0.8rem; font-weight: 700; cursor: pointer; transition: all 0.2s; color: $GRAY-COLD; }
.theme_dark .pill_btn { color: $GRAY-LIGHT; }
.pill_btn.activo { background: $PRIMARY-PURPLE; color: $WHITE; box-shadow: $shadow-purple; }
.pill_btn.optimizado.activo { background: $SUCCESS-COLOR; box-shadow: 0 4px 12px rgba(26, 188, 156, 0.3); }
.pill_btn.puro.activo { background: $WARNING-COLOR; color: #333; box-shadow: 0 4px 12px rgba(255, 193, 7, 0.3); }

.action_group { display: flex; align-items: center; gap: 20px; }

.btn_extract { background: $GRADIENT; color: $WHITE; border: none; padding: 10px 24px; border-radius: 10px; font-weight: 800; cursor: pointer; transition: all 0.2s; }
.btn_extract:disabled { background: $INACTIVE-COLOR; cursor: not-allowed; opacity: 0.5; }
.btn_extract:not(:disabled):hover { transform: translateY(-2px); filter: brightness(1.1); box-shadow: $shadow-purple; }

.limits_panel { margin-top: 16px; padding-top: 16px; border-top: 1px dashed rgba(153, 162, 173, 0.3); display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.limits_title { font-size: 0.85rem; font-weight: 800; color: $PRIMARY-PURPLE; text-transform: uppercase; }
.limit_box { display: flex; flex-direction: column; gap: 4px; }
.limit_box label { font-size: 0.75rem; font-weight: 700; color: $GRAY-COLD; }
.limit_input { width: 90px; padding: 6px 10px; border-radius: 8px; border: 1px solid; font-weight: 700; font-size: 0.9rem; text-align: center; }
.theme_light .limit_input { background: $WHITE-SOFT; border-color: $LIGHT-BORDER; color: $DARK-TEXT; }
.theme_dark .limit_input { background: $DARK-INPUT-BG; border-color: rgba(255, 255, 255, 0.1); color: $WHITE; }

.metrics_bar { display: flex; align-items: center; padding-top: 12px; border-top: 1px solid rgba(153, 162, 173, 0.1); }
.metrics_scroll { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 8px; }
.metrics_scroll::-webkit-scrollbar { height: 4px; }
.metrics_scroll::-webkit-scrollbar-thumb { background: $GRAY-COLD; border-radius: 4px; }

.metric_chip { display: flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 20px; cursor: pointer; white-space: nowrap; transition: all 0.2s; border: 1px solid transparent; }
.theme_light .metric_chip { background: rgba(0,0,0,0.03); color: $DARK-TEXT; }
.theme_dark .metric_chip { background: rgba(255,255,255,0.05); color: $LIGHT-TEXT; }
.metric_chip:hover { background: rgba(138, 43, 226, 0.1); color: $PRIMARY-PURPLE; }
.metric_chip.activo { background: rgba(138, 43, 226, 0.15); border-color: $PRIMARY-PURPLE; color: $PRIMARY-PURPLE; }
.m_name { font-weight: 700; font-size: 0.8rem; }
.m_unit { font-size: 0.65rem; opacity: 0.7; }

.switch_wrapper { display: flex; align-items: center; cursor: pointer; }
.switch { position: relative; display: inline-block; width: 40px; height: 22px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: $INACTIVE-COLOR; transition: .3s; border-radius: 34px; }
.slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 3px; bottom: 3px; background-color: $WHITE; transition: .3s; border-radius: 50%; }
input:checked + .slider { background: $GRADIENT; }
input:disabled + .slider { opacity: 0.5; cursor: not-allowed; }
input:checked + .slider:before { transform: translateX(18px); }

/* GRID DE TARJETAS INDICADORAS */
.kpi_summary_grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 16px; }
.kpi_card { border-radius: 12px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; transition: transform 0.2s ease; }
.kpi_card:hover { transform: translateY(-2px); }
.theme_light .kpi_card { background: $WHITE; border: 1px solid $LIGHT-BORDER; box-shadow: $shadow-soft; }
.theme_dark .kpi_card { background: $SUBTLE-BG-DARK; border: 1px solid $DARK-BORDER; box-shadow: $shadow-dark; }

.kpi_header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.icon_wrap { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; }
.kpi_title { font-weight: 800; font-size: 0.85rem; }
.theme_dark .kpi_title { color: $WHITE; }

.kpi_body { margin-bottom: 8px; }
.kpi_value { font-size: 1.8rem; font-weight: 900; line-height: 1; }
.kpi_unit { font-size: 0.85rem; font-weight: 700; color: $GRAY-COLD; }

.kpi_footer { border-color: rgba(153, 162, 173, 0.15) !important; }
.kpi_minmax { display: flex; justify-content: space-between; align-items: center; }
.theme_dark .kpi_minmax strong { color: $LIGHT-TEXT; }

.text-danger { color: $DANGER-COLOR !important; }
.text-info { color: #3498DB !important; }
.text-success { color: $SUCCESS-COLOR !important; }
.text-warning { color: $WARNING-COLOR !important; }
.text-primary { color: $PRIMARY-PURPLE !important; }

.icon_wrap.text-danger { background: rgba(231, 76, 60, 0.1); }
.icon_wrap.text-info { background: rgba(52, 152, 219, 0.1); }
.icon_wrap.text-success { background: rgba(26, 188, 156, 0.1); }
.icon_wrap.text-warning { background: rgba(255, 193, 7, 0.1); }
.icon_wrap.text-primary { background: rgba(138, 43, 226, 0.1); }

.charts_grid_multiple { display: grid; gap: 20px; grid-template-columns: repeat(2, 1fr); }
.charts_grid_single { display: grid; grid-template-columns: 1fr; }
.grid_item { width: 100%; }
.span_2 { grid-column: span 2; }
.span_1 { grid-column: span 1; }

.empty_state { border-radius: 16px; }
.theme_light .empty_state { background: $WHITE; }
.theme_dark .empty_state { background: $SUBTLE-BG-DARK; }
.empty_icon { width: 80px; height: 80px; border-radius: 20px; background: rgba(138, 43, 226, 0.1); color: $PRIMARY-PURPLE; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; margin: 0 auto; }
.text_light { color: $DARK-TEXT; }
.theme_dark .text_light { color: $WHITE; }
.text_muted { color: $GRAY-COLD; }

@media (max-width: 1200px) {
  .charts_grid_multiple { grid-template-columns: 1fr; }
  .span_1 { grid-column: span 1; }
  .span_2 { grid-column: span 1; }
  .toolbar_top { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 768px) {
  .plataforma_contenido { margin-left: 0; padding: 15px; }
  .header_dashboard { flex-direction: column; align-items: flex-start; }
  .date_group { flex-direction: column; align-items: stretch; width: 100%; }
  .action_group { width: 100%; justify-content: space-between; }
}
</style>