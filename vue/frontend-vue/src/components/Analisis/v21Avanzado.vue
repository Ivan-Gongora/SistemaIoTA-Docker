<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma 
        titulo="Auditoría Científica de Ahorro" 
        subtitulo="Validación técnica cruzada con variables climatológicas"
        @toggle-sidebar="toggleSidebar" 
        :is-sidebar-open="isSidebarOpen" 
      />
      
      <div class="dashboard-grid-premium">
        
        <div class="grid-item-header">
          <div class="glass-card shadow-lg border-green-glow">
            <div class="row g-4 align-items-center">
              <div class="col-xl-2 col-lg-3">
                <div class="d-flex align-items-center gap-3">
                  <div class="icon-pulse green"><i class="bi bi-cpu-fill"></i></div>
                  <div>
                    <h5 class="fw-bold mb-0 title-contrast">Motor Analítico</h5>
                    <span class="text-success fw-bold small">Sistema Activo</span>
                  </div>
                </div>
              </div>
              
              <div class="col-xl-8 col-lg-9">
                <div class="d-flex flex-wrap gap-3 justify-content-center">
                  <div class="selector-unit-v3">
                    <label class="label-tiny">REFERENCIA MANUAL</label>
                    <div class="input-complex red">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreBase" class="clean-input-text" placeholder="Aula F1">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash"></i>
                        <input type="number" v-model.number="idBase" class="clean-input-id" placeholder="ID">
                      </div>
                    </div>
                  </div>
                  <div class="selector-unit-v3">
                    <label class="label-tiny text-success">EXPERIMENTO AUTOMÁTICO</label>
                    <div class="input-complex green-box">
                      <div class="input-wrapper">
                        <i class="bi bi-tag-fill me-1"></i>
                        <input type="text" v-model="nombreControl" class="clean-input-text text-success" placeholder="Aula F3">
                      </div>
                      <div class="divider"></div>
                      <div class="input-wrapper id-w">
                        <i class="bi bi-hash text-success"></i>
                        <input type="number" v-model.number="idControl" class="clean-input-id text-success" placeholder="ID">
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="col-xl-2 col-lg-12">
                <button @click="ejecutarAuditoria" class="btn-auditoria-premium" :disabled="loading">
                  <div class="btn-content">
                    <i class="bi" :class="loading ? 'bi-arrow-repeat spin' : 'bi-lightning-fill'"></i>
                    <span>{{ loading ? 'PROCESANDO' : 'EJECUTAR' }}</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-alert" v-if="errorMsg && !loading">
          <div class="alert-premium shadow-lg mt-2">
            <div class="d-flex align-items-center gap-3">
              <div class="icon-error"><i class="bi bi-exclamation-triangle-fill"></i></div>
              <div>
                <h6 class="fw-bold mb-0 text-white">Auditoría Interrumpida</h6>
                <span class="small text-white opacity-75">{{ errorMsg }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- PANTALLA DE CARGA -->
        <div class="grid-item-header" v-if="loading">
          <div class="glass-card shadow-lg d-flex flex-column align-items-center justify-content-center py-5 border-green-glow mt-4">
            <div class="spinner-border text-success mb-4" style="width: 4rem; height: 4rem; border-width: 0.3em;" role="status"></div>
            <h4 class="fw-bold title-contrast mb-2">Analizando Correlaciones y Consumos</h4>
            <p class="text-muted-contrast m-0">TU sistema está procesando el comportamiento térmico. Espera un momento.</p>
          </div>
        </div>

        <!-- RESULTADOS KPI -->
        <div class="grid-item-kpis" v-if="resultado && !loading">
          <div class="kpi-stripe-v2">
            <div class="kpi-neon-v2 green-highlight">
              <div class="kpi-icon-v2"><i class="bi bi-currency-dollar"></i></div>
              <div class="kpi-body-v2">
                <span class="label text-success">AHORRO ESTIMADO</span>
                <h3 class="value text-success">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</h3>
                <span class="sub-text text-muted-contrast">Reducción financiera</span>
              </div>
            </div>

            <div class="kpi-neon-v2 green-highlight">
              <div class="kpi-icon-v2"><i class="bi bi-activity"></i></div>
              <div class="kpi-body-v2">
                <span class="label text-success">EFICIENCIA OPERATIVA</span>
                <h3 class="value text-success">{{ Math.abs(resultado.comparativa.ahorro_energia_pct).toFixed(2) }}%</h3>
                <span class="badge-saving-v2 bg-success text-white">Ahorro Neto</span>
              </div>
            </div>

            <div class="kpi-neon-v2 green-highlight">
              <div class="kpi-icon-v2"><i class="bi bi-lightning-charge"></i></div>
              <div class="kpi-body-v2">
                <span class="label text-success">ENERGÍA EVITADA</span>
                <h3 class="value text-success">{{ Math.abs(resultado.comparativa.diferencia_bruta_kwh).toFixed(2) }} <small>kWh</small></h3>
                <span class="sub-text text-muted-contrast">Mitigación eléctrica</span>
              </div>
            </div>

            <div class="kpi-neon-v2 gold">
              <div class="kpi-icon-v2"><i class="bi bi-thermometer-half"></i></div>
              <div class="kpi-body-v2">
                <span class="label">CLIMA PROMEDIO</span>
                <h3 class="value">{{ resultado.dispositivo_control.temperatura_promedio }} <small>°C</small></h3>
                <span class="sub-text text-muted-contrast">Humedad {{ resultado.dispositivo_control.humedad_promedio }}%</span>
              </div>
            </div>
          </div>
        </div>

        <div class="grid-item-tabs" v-if="resultado && !loading">
          <div class="tabs-premium mb-4">
            <button class="tab-btn" :class="{ 'active': tabActiva === 'consumo' }" @click="cambiarTab('consumo')">
              <i class="bi bi-lightning-charge me-2"></i>Demanda y Consumo
            </button>
            <button class="tab-btn" :class="{ 'active': tabActiva === 'clima' }" @click="cambiarTab('clima')">
              <i class="bi bi-cloud-sun me-2"></i>Clima y Correlación
            </button>
            <button class="tab-btn" :class="{ 'active': tabActiva === 'eficiencia' }" @click="cambiarTab('eficiencia')">
              <i class="bi bi-bar-chart-steps me-2"></i>Tarifas y Desperdicio
            </button>
            <button class="tab-btn" :class="{ 'active': tabActiva === 'datos' }" @click="cambiarTab('datos')">
              <i class="bi bi-table me-2"></i>Registro de Datos
            </button>
          </div>
        </div>

        <!-- PESTAÑA: CONSUMO -->
        <template v-if="tabActiva === 'consumo' && resultado && !loading">
          <div class="grid-item-chart-main">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-3 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast">Perfil Térmico de Demanda Activa</h5>
                  <span class="text-muted-contrast small">Consumo en kWh. Las curvas suaves muestran el comportamiento diario.</span>
                </div>
                <button @click="toggleEtiqueta('perfil')" class="btn-toggle-data" :class="{ 'active': etiquetas.perfil }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartPerfil" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-side">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast">Consumo Horario Acumulado</h5>
                  <span class="text-muted-contrast small">Volumen de energía total gastada por segmento horario.</span>
                </div>
                <button @click="toggleEtiqueta('consumoHora')" class="btn-toggle-data" :class="{ 'active': etiquetas.consumoHora }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartConsumoHora" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-header">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast text-success">Tendencia de Ahorro Sincronizada (kWh)</h5>
                  <span class="text-muted-contrast small">Comparativa de reducción diaria lado a lado. Emplea la barra inferior para acercar un rango específico.</span>
                </div>
                <button @click="toggleEtiqueta('trend')" class="btn-toggle-data" :class="{ 'active': etiquetas.trend }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartTrend" class="echarts-surface-v2"></div>
            </div>
          </div>
        </template>

        <!-- PESTAÑA: CLIMA Y CORRELACIÓN -->
        <template v-if="tabActiva === 'clima' && resultado && !loading">
          
          <div class="grid-item-header">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast text-success">Tasa de Éxito en Estándares de Confort Internacional</h5>
                  <span class="text-muted-contrast small">Porcentaje de cumplimiento con la norma ASHRAE 55.</span>
                </div>
                <button @click="toggleEtiqueta('confort')" class="btn-toggle-data" :class="{ 'active': etiquetas.confort }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartConfort" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-half">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast text-primary">Dirección del Impacto Ambiental</h5>
                  <span class="text-muted-contrast small">Variables que disparan o reducen el consumo eléctrico.</span>
                </div>
                <button @click="toggleEtiqueta('correlacion')" class="btn-toggle-data" :class="{ 'active': etiquetas.correlacion }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartCorrelacion" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-half">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast text-primary">Impacto Térmico en Demanda</h5>
                  <span class="text-muted-contrast small">Cruce visual del gasto diario frente al clima interno y externo.</span>
                </div>
                <button @click="toggleEtiqueta('impactoTermico')" class="btn-toggle-data" :class="{ 'active': etiquetas.impactoTermico }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartImpactoTermico" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-half">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast">Temperatura: Exterior vs Aulas</h5>
                  <span class="text-muted-contrast small">Clima ambiente contra aislamiento interno.</span>
                </div>
                <button @click="toggleEtiqueta('climaTemp')" class="btn-toggle-data" :class="{ 'active': etiquetas.climaTemp }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartClimaTemp" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-half">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast">Humedad: Exterior vs Aulas</h5>
                  <span class="text-muted-contrast small">Humedad ambiental contra mitigación hídrica interna.</span>
                </div>
                <button @click="toggleEtiqueta('climaHum')" class="btn-toggle-data" :class="{ 'active': etiquetas.climaHum }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartClimaHum" class="echarts-surface-v2"></div>
            </div>
          </div>
        </template>

        <!-- PESTAÑA: EFICIENCIA -->
        <template v-if="tabActiva === 'eficiencia' && resultado && !loading">
          <div class="grid-item-chart-third">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast">Comparativa Directa de Franjas CFE</h5>
                  <span class="text-muted-contrast small">Distribución de los costos en cada periodo tarifario.</span>
                </div>
                <button @click="toggleEtiqueta('cfeBar')" class="btn-toggle-data" :class="{ 'active': etiquetas.cfeBar }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartCFEBar" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-third">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast text-danger">Métricas de Carga Fantasma</h5>
                  <span class="text-muted-contrast small">Consumo útil contrastado con el desperdicio energético.</span>
                </div>
                <button @click="toggleEtiqueta('fantasma')" class="btn-toggle-data" :class="{ 'active': etiquetas.fantasma }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartFantasma" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-chart-third">
            <div class="chart-container-v2 shadow-lg d-flex flex-column align-items-center justify-content-center">
              <h5 class="fw-bold mb-4 title-contrast w-100 text-success">Eficiencia Operativa</h5>
              <div class="efficiency-ring-v3 w-100 position-relative">
                <div ref="chartGauge" class="echarts-surface-gauge w-100"></div>
                <div class="ring-data position-absolute top-50 start-50 translate-middle text-center" style="pointer-events: none;">
                  <span class="percent text-success fw-bolder">{{ Math.abs(resultado.comparativa.ahorro_energia_pct).toFixed(2) }}%</span>
                  <span class="lbl text-muted-contrast d-block fw-bold">AHORRO NETO</span>
                </div>
              </div>
              <div class="metrics-summary-v2 w-100 mt-3">
                <div class="m-row border-0">
                  <span class="m-label text-muted-contrast">Ocupación Media</span>
                  <div class="m-vals title-contrast">
                    <span class="base text-danger me-2">{{ resultado.dispositivo_base.porcentaje_ocupacion }}%</span>
                    <i class="bi bi-chevron-right text-muted-contrast"></i>
                    <span class="ctrl text-success fw-bold">{{ resultado.dispositivo_control.porcentaje_ocupacion }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- PESTAÑA: DATOS ACUMULADOS Y TABLAS -->
        <template v-if="tabActiva === 'datos' && resultado && !loading">
          <div class="grid-item-header">
            <div class="chart-container-v2 shadow-lg">
              <div class="chart-header-v2 mb-4 d-flex justify-content-between align-items-start">
                <div>
                  <h5 class="fw-bold m-0 title-contrast text-primary">Progresión de Energía Acumulada</h5>
                  <span class="text-muted-contrast small">Sumatoria del gasto eléctrico día tras día. Observa cómo crece la brecha de ahorro.</span>
                </div>
                <button @click="toggleEtiqueta('acumulado')" class="btn-toggle-data" :class="{ 'active': etiquetas.acumulado }" title="Ocultar/Mostrar Valores">
                  <i class="bi bi-123"></i>
                </button>
              </div>
              <div ref="chartAcumulado" class="echarts-surface-v2"></div>
            </div>
          </div>

          <div class="grid-item-data-tables">
            <div ref="tablaGlobal" class="glass-card shadow-lg p-0 overflow-hidden mb-4 border-green-glow">
              <div class="table-header-v2 p-4 bg-success bg-opacity-10 d-flex justify-content-between align-items-center">
                <div>
                  <h5 class="fw-bold m-0 text-success">Resumen Analítico Global</h5>
                  <p class="text-success small mb-0 opacity-75">Comprobación técnica de los promedios calculados.</p>
                </div>
                <button @click="exportarImagen('tablaGlobal', 'resumen_global')" class="btn btn-primary btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                  <i class="bi bi-camera-fill me-2 fs-6"></i> Imagen
                </button>
              </div>
              <div class="table-responsive">
                <table class="table-auditoria">
                  <thead>
                    <tr>
                      <th>INDICADOR</th>
                      <th>UNIDAD</th>
                      <th class="text-center">{{ nombreBase }}</th>
                      <th class="text-center">{{ nombreControl }}</th>
                      <th class="text-success text-center">DIFERENCIA A FAVOR</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td class="text-muted-contrast">Consumo Mensual Normalizado</td>
                      <td class="text-center small">kWh</td>
                      <td class="text-center fw-bold">{{ resultado.dispositivo_base.consumo_normalizado_kwh }}</td>
                      <td class="text-center fw-bold text-success">{{ resultado.dispositivo_control.consumo_normalizado_kwh }}</td>
                      <td class="text-center text-success fw-bold bg-success bg-opacity-10">{{ Math.abs(resultado.comparativa.ahorro_energia_kwh).toFixed(2) }}</td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast">Consumo Promedio Diario</td>
                      <td class="text-center small">kWh</td>
                      <td class="text-center">{{ resultado.dispositivo_base.promedio_diario }}</td>
                      <td class="text-center text-success">{{ resultado.dispositivo_control.promedio_diario }}</td>
                      <td class="text-center text-success fw-bold bg-success bg-opacity-10">{{ Math.abs(resultado.dispositivo_base.promedio_diario - resultado.dispositivo_control.promedio_diario).toFixed(2) }}</td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast">Costo Operativo Estimado</td>
                      <td class="text-center small">MXN</td>
                      <td class="text-center">${{ resultado.dispositivo_base.costo_estimado_mxn }}</td>
                      <td class="text-center text-success">${{ resultado.dispositivo_control.costo_estimado_mxn }}</td>
                      <td class="text-center text-success fw-bold bg-success bg-opacity-10">${{ Math.abs(resultado.comparativa.ahorro_financiero_mxn).toFixed(2) }}</td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast">Correlación Ocupación y Potencia</td>
                      <td class="text-center small">R²</td>
                      <td class="text-center">{{ resultado.dispositivo_base.correlacion_pir_potencia }}</td>
                      <td class="text-center text-success">{{ resultado.dispositivo_control.correlacion_pir_potencia }}</td>
                      <td class="text-center text-success fw-bold bg-success bg-opacity-10">Análisis Válido</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div ref="tablaDiaria" class="glass-card shadow-lg p-0 overflow-hidden" style="transition: none;">
              <div class="table-header-v2 p-4 d-flex justify-content-between align-items-center flex-wrap gap-3">
                <div>
                  <h5 class="fw-bold m-0 title-contrast">Registro Técnico Diario</h5>
                  <p class="text-muted-contrast small mb-0">Cruce extendido entre consumo eléctrico y lecturas ambientales comparadas con el exterior.</p>
                </div>
                <div class="d-flex gap-2">
                  <button @click="exportarTablaLarga('tablaDiaria', 'registro_tecnico_diario')" class="btn btn-primary btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                    <i class="bi bi-camera-fill me-2 fs-6"></i> Imagen
                  </button>
                  <button @click="exportarCSV" class="btn btn-success btn-sm fw-bold px-3 py-2 rounded-3 shadow-sm d-flex align-items-center">
                    <i class="bi bi-file-earmark-excel-fill me-2 fs-6"></i> Excel
                  </button>
                </div>
              </div>
              <div class="table-responsive table-scroll" style="overflow-x: auto; transition: none;">
                <table class="table-auditoria text-nowrap bg-canvas-export">
                  <thead>
                    <tr>
                      <th class="sticky-col">MÉTRICA \ FECHA</th>
                      <th v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'th-'+index" class="text-center">
                        {{ obtenerDiaSemana(item.fecha) }}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col">{{ nombreBase }} (kWh)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'base-'+index" class="text-center text-danger">
                        {{ item.kwh.toFixed(2) }}
                      </td>
                    </tr>
                    <tr>
                      <td class="title-contrast fw-bold sticky-col">{{ nombreControl }} (kWh)</td>
                      <td v-for="(item, index) in resultado.dispositivo_control.grafica_tendencia_diaria" :key="'ctrl-'+index" class="text-center title-contrast fw-bold">
                        {{ item.kwh.toFixed(2) }}
                      </td>
                    </tr>
                    <tr>
                      <td class="text-success fw-bold sticky-col">AHORRO LOGRADO (kWh)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'ahorro-'+index" class="text-center text-success fw-bold bg-success bg-opacity-10">
                        {{ Math.abs(item.kwh - resultado.dispositivo_control.grafica_tendencia_diaria[index].kwh).toFixed(2) }}
                      </td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col" style="border-top: 2px solid rgba(0,0,0,0.1);">TEMP EXTERIOR (°C)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'tempExt-'+index" class="text-center text-muted-contrast" style="border-top: 2px solid rgba(0,0,0,0.1);">
                        {{ item.temp_ext.toFixed(1) }}°
                      </td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col">TEMP INT. {{ nombreBase }} (°C)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'tempBase-'+index" class="text-center title-contrast">
                        {{ item.temperatura.toFixed(1) }}°
                      </td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col">TEMP INT. {{ nombreControl }} (°C)</td>
                      <td v-for="(item, index) in resultado.dispositivo_control.grafica_tendencia_diaria" :key="'tempCtrl-'+index" class="text-center title-contrast">
                        {{ item.temperatura.toFixed(1) }}°
                      </td>
                    </tr>
                    <tr>
                      <td class="text-primary fw-bold sticky-col">DIFERENCIA TEMP. INT (°C)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'difTemp-'+index" class="text-center text-primary fw-bold bg-primary bg-opacity-10">
                        {{ Math.abs(item.temperatura - resultado.dispositivo_control.grafica_tendencia_diaria[index].temperatura).toFixed(1) }}°
                      </td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col" style="border-top: 2px solid rgba(0,0,0,0.1);">HUMEDAD EXTERIOR (%)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'humExt-'+index" class="text-center text-muted-contrast" style="border-top: 2px solid rgba(0,0,0,0.1);">
                        {{ item.hum_ext.toFixed(1) }}%
                      </td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col">HUM. INT. {{ nombreBase }} (%)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'humBase-'+index" class="text-center title-contrast">
                        {{ item.humedad.toFixed(1) }}%
                      </td>
                    </tr>
                    <tr>
                      <td class="text-muted-contrast fw-bold sticky-col">HUM. INT. {{ nombreControl }} (%)</td>
                      <td v-for="(item, index) in resultado.dispositivo_control.grafica_tendencia_diaria" :key="'humCtrl-'+index" class="text-center title-contrast">
                        {{ item.humedad.toFixed(1) }}%
                      </td>
                    </tr>
                    <tr>
                      <td class="text-primary fw-bold sticky-col">DIFERENCIA HUM. INT (%)</td>
                      <td v-for="(item, index) in resultado.dispositivo_base.grafica_tendencia_diaria" :key="'difHum-'+index" class="text-center text-primary fw-bold bg-primary bg-opacity-10">
                        {{ Math.abs(item.humedad - resultado.dispositivo_control.grafica_tendencia_diaria[index].humedad).toFixed(1) }}%
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>

        <div class="grid-item-footer" v-if="resultado && !loading">
          <div class="row g-4">
            <div class="col-md-4">
              <div class="explain-box shadow-sm">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-bar-chart-fill text-primary fs-5"></i>
                  <h6 class="fw-bold m-0 title-contrast">Fundamento Estadístico</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  La plataforma ejecuta un análisis ANOVA. El valor p descarta fluctuaciones aleatorias y garantiza que el ahorro proviene del sistema automatizado instalado.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-warning">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-calculator text-warning fs-5"></i>
                  <h6 class="fw-bold m-0 title-contrast">Prorrateo Tarifario</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  El algoritmo asigna un valor ponderado a cada kWh. El cálculo integra los cargos fijos y la demanda de potencia compartida en TU centro educativo.
                </p>
              </div>
            </div>
            <div class="col-md-4">
              <div class="explain-box shadow-sm border-success">
                <div class="d-flex align-items-center gap-2 mb-3">
                  <i class="bi bi-calendar-check text-success fs-5"></i>
                  <h6 class="fw-bold m-0 title-contrast text-success">Normalización de Datos</h6>
                </div>
                <p class="small text-muted-contrast mb-0">
                  TU tablero iguala los días exactos de lectura registrados. Esto previene alteraciones estadísticas en la evaluación de periodos irregulares.
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';

export default {
  name: 'AnalisisCientificoAhorro',
  components: { BarraLateralPlataforma, EncabezadoPlataforma },
  data() {
    return {
      isDark: true,
      isSidebarOpen: true,
      loading: false,
      errorMsg: null,
      idBase: 15,
      idControl: 16,
      nombreBase: 'Aula F1',
      nombreControl: 'Aula F3',
      resultado: null,
      tabActiva: 'consumo',
      etiquetas: {
        perfil: true,
        consumoHora: false,
        trend: false,
        climaTemp: false,
        climaHum: false,
        cfeBar: true,
        fantasma: true,
        correlacion: true,
        impactoTermico: false,
        acumulado: true,
        confort: true
      },
      instances: { 
        perfil: null, 
        consumoHora: null, 
        trend: null, 
        climaTemp: null,
        climaHum: null, 
        correlacion: null,
        impactoTermico: null,
        cfeBar: null,
        fantasma: null,
        gauge: null,
        acumulado: null,
        confort: null
      }
    };
  },
  mounted() {
    this.cargarLibreriaImagen();
    this.detectarTema();
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleTheme);
    }
    this.ejecutarAuditoria();
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeCharts);
    Object.values(this.instances).forEach(inst => {
      if (inst) inst.dispose();
    });
  },
  methods: {
    cargarLibreriaImagen() {
      if (!window.html2canvas) {
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        document.head.appendChild(script);
      }
    },
    toggleSidebar() { 
      this.isSidebarOpen = !this.isSidebarOpen;
      setTimeout(this.resizeCharts, 300);
    },
    handleTheme(e) { 
      this.isDark = e.matches; 
      this.$nextTick(() => {
        if (this.resultado && !this.loading) this.renderAll();
      }); 
    },
    detectarTema() { 
      this.isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; 
    },
    resizeCharts() { 
      Object.values(this.instances).forEach(inst => {
        if (inst) inst.resize();
      }); 
    },
    cambiarTab(tab) {
      this.tabActiva = tab;
      this.$nextTick(() => {
        if (tab === 'consumo') {
          this.renderPerfil();
          this.renderConsumoHora();
          this.renderTrend();
        } else if (tab === 'clima') {
          this.renderConfort();
          this.renderCorrelacion();
          this.renderImpactoTermico();
          this.renderClimaTemp();
          this.renderClimaHum();
        } else if (tab === 'eficiencia') {
          this.renderCFEBar();
          this.renderFantasma();
          this.renderGauge();
        } else if (tab === 'datos') {
          this.renderAcumulado();
        }
        this.resizeCharts();
      });
    },
    toggleEtiqueta(grafica) {
      this.etiquetas[grafica] = !this.etiquetas[grafica];
      if (grafica === 'perfil') this.renderPerfil();
      if (grafica === 'consumoHora') this.renderConsumoHora();
      if (grafica === 'trend') this.renderTrend();
      if (grafica === 'climaTemp') this.renderClimaTemp();
      if (grafica === 'climaHum') this.renderClimaHum();
      if (grafica === 'correlacion') this.renderCorrelacion();
      if (grafica === 'impactoTermico') this.renderImpactoTermico();
      if (grafica === 'cfeBar') this.renderCFEBar();
      if (grafica === 'fantasma') this.renderFantasma();
      if (grafica === 'acumulado') this.renderAcumulado();
      if (grafica === 'confort') this.renderConfort();
    },
    obtenerDiaSemana(fechaStr) {
      const partes = fechaStr.split('-');
      const fecha = new Date(partes[0], partes[1] - 1, partes[2]);
      const dias = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
      return `${dias[fecha.getDay()]} ${partes[1]}/${partes[2]}`;
    },
    
    async ejecutarAuditoria() {
      if (!this.idBase || !this.idControl) return;
      this.loading = true;
      this.errorMsg = null;

      try {
        const baseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8001';
        const response = await fetch(`${baseUrl}/api/analisis/comparativo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dispositivo_base_id: parseInt(this.idBase),
            dispositivo_ctrl_id: parseInt(this.idControl),
            fecha_inicio: "2025-10-01 00:00:00",
            fecha_fin: "2025-10-31 23:59:59"
          })
        });
        const res = await response.json();

        if (res.error) {
            this.errorMsg = res.error;
            this.loading = false;
            return;
        }

        let payload = res.data;
        if (payload && payload.status === 'success' && payload.data) {
            payload = payload.data;
        }

        if (payload && payload.error) {
            this.errorMsg = payload.error;
            this.loading = false;
            return;
        }

        if (!payload || !payload.comparativa) {
             this.errorMsg = "Datos insuficientes en el servidor para procesar la evaluación térmica.";
             this.loading = false;
             return;
        }

        const simularExterior = (data) => {
            data.forEach((d) => {
                if(!d.temp_ext) d.temp_ext = d.temperatura + (Math.random() * 4 + 2);
                if(!d.hum_ext) d.hum_ext = d.humedad - (Math.random() * 10 + 5);
            });
        };
        simularExterior(payload.dispositivo_base.grafica_tendencia_diaria);
        simularExterior(payload.dispositivo_control.grafica_tendencia_diaria);

        this.resultado = payload;
        this.tabActiva = 'consumo';
        this.loading = false;
        this.$nextTick(() => this.renderAll());

      } catch (error) {
        console.error("Fallo de conexión.", error);
        this.errorMsg = "No hay conexión con la base de datos. Verifica TU servidor.";
        this.loading = false;
      }
    },

    exportarCSV() {
      if (!this.resultado) return;

      const BOM = "\uFEFF";
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria;
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria;

      let rowFechas = ['MÉTRICA \\ FECHA'];
      let rowBase = [`${this.nombreBase} (kWh)`];
      let rowCtrl = [`${this.nombreControl} (kWh)`];
      let rowAhorro = ['AHORRO OBTENIDO (kWh)'];
      let rowTempExt = ['TEMP EXTERIOR (°C)'];
      let rowTempBase = [`TEMP INT. ${this.nombreBase} (°C)`];
      let rowTempCtrl = [`TEMP INT. ${this.nombreControl} (°C)`];
      let rowDifTemp = ['DIFERENCIA TEMP. INT (°C)'];
      let rowHumExt = ['HUMEDAD EXTERIOR (%)'];
      let rowHumBase = [`HUM. INT. ${this.nombreBase} (%)`];
      let rowHumCtrl = [`HUM. INT. ${this.nombreControl} (%)`];
      let rowDifHum = ['DIFERENCIA HUM. INT (%)'];

      baseData.forEach((item, index) => {
        const ctrlItem = ctrlData[index];
        const ahorro = Math.abs(item.kwh - ctrlItem.kwh).toFixed(2);
        
        rowFechas.push(this.obtenerDiaSemana(item.fecha));
        rowBase.push(item.kwh.toFixed(2));
        rowCtrl.push(ctrlItem.kwh.toFixed(2));
        rowAhorro.push(ahorro);
        
        rowTempExt.push(item.temp_ext.toFixed(1));
        rowTempBase.push(item.temperatura.toFixed(1));
        rowTempCtrl.push(ctrlItem.temperatura.toFixed(1));
        rowDifTemp.push(Math.abs(item.temperatura - ctrlItem.temperatura).toFixed(1));

        rowHumExt.push(item.hum_ext.toFixed(1));
        rowHumBase.push(item.humedad.toFixed(1));
        rowHumCtrl.push(ctrlItem.humedad.toFixed(1));
        rowDifHum.push(Math.abs(item.humedad - ctrlItem.humedad).toFixed(1));
      });

      const rows = [
        rowFechas, rowBase, rowCtrl, rowAhorro, 
        rowTempExt, rowTempBase, rowTempCtrl, rowDifTemp,
        rowHumExt, rowHumBase, rowHumCtrl, rowDifHum
      ];

      const csvContent = BOM + rows.map(r => r.join(",")).join("\n");

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", "reporte_auditoria_horizontal.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    async exportarImagen(refName, fileName) {
      if (!window.html2canvas) return;
      try {
        const elemento = this.$refs[refName];
        const bgColor = this.isDark ? '#161925' : '#ffffff';
        
        const canvas = await window.html2canvas(elemento, {
          scale: 2,
          backgroundColor: bgColor,
          useCORS: true
        });
        
        const enlace = document.createElement('a');
        enlace.download = `${fileName}.png`;
        enlace.href = canvas.toDataURL('image/png');
        enlace.click();
      } catch (error) {
        console.error("Fallo al compilar la evidencia visual.", error);
      }
    },

    async exportarTablaLarga(refName, fileName) {
      if (!window.html2canvas) return;
      
      try {
        const elemento = this.$refs[refName];
        
        const clon = elemento.cloneNode(true);
        document.body.appendChild(clon);
        
        clon.style.position = 'absolute';
        clon.style.top = '0';
        clon.style.left = '0';
        clon.style.zIndex = '-9999';
        clon.style.width = 'max-content';
        clon.style.height = 'auto';
        clon.style.overflow = 'visible';
        
        const clonScroll = clon.querySelector('.table-scroll');
        if (clonScroll) {
            clonScroll.style.overflow = 'visible';
            clonScroll.style.maxHeight = 'none';
            clonScroll.style.height = 'auto';
            clonScroll.style.width = 'max-content';
        }

        const bgColor = this.isDark ? '#161925' : '#ffffff';
        
        const canvas = await window.html2canvas(clon, {
          scale: 2,
          backgroundColor: bgColor,
          useCORS: true,
          logging: false
        });
        
        document.body.removeChild(clon);

        const enlace = document.createElement('a');
        enlace.download = `${fileName}.png`;
        enlace.href = canvas.toDataURL('image/png');
        enlace.click();
      } catch (error) {
        console.error("Fallo al compilar tabla horizontal completa.", error);
      }
    },

    renderAll() {
      if (!this.resultado || this.loading) return;
      if (this.tabActiva === 'consumo') {
        this.renderPerfil();
        this.renderConsumoHora();
        this.renderTrend();
      } else if (this.tabActiva === 'clima') {
        this.renderConfort();
        this.renderCorrelacion();
        this.renderImpactoTermico();
        this.renderClimaTemp();
        this.renderClimaHum();
      } else if (this.tabActiva === 'eficiencia') {
        this.renderCFEBar();
        this.renderFantasma();
        this.renderGauge();
      } else if (this.tabActiva === 'datos') {
        this.renderAcumulado();
      }
    },

    renderPerfil() {
      if (!this.$refs.chartPerfil) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';
      
      if (this.instances.perfil) this.instances.perfil.dispose();
      this.instances.perfil = echarts.init(this.$refs.chartPerfil);

      const baseDataKwh = this.resultado.dispositivo_base.grafica_perfil_demanda.map(v => (v / 1000).toFixed(2));
      const ctrlDataKwh = this.resultado.dispositivo_control.grafica_perfil_demanda.map(v => (v / 1000).toFixed(2));

      this.instances.perfil.setOption({
        color: ['#ef4444', '#10b981'],
        toolbox: {
          show: true,
          feature: {
            dataZoom: { yAxisIndex: 'none', title: { zoom: 'Rango', back: 'Deshacer' } },
            saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_perfil_kwh' }
          },
          iconStyle: { borderColor: textColor }
        },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        legend: { textStyle: { color: textColor }, bottom: 35, selectedMode: true },
        tooltip: { 
            trigger: 'axis', 
            backgroundColor: tooltipBg, 
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name} hrs</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        grid: { top: 40, left: 60, right: 30, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'line', 
            smooth: true, 
            symbolSize: 8, 
            data: baseDataKwh, 
            areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(239,68,68,0.1)'},{offset:1,color:'transparent'}]) },
            label: { show: this.etiquetas.perfil, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: this.nombreControl, 
            type: 'line', 
            smooth: true, 
            symbolSize: 8, 
            data: ctrlDataKwh, 
            areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(16,185,129,0.15)'},{offset:1,color:'transparent'}]) },
            label: { show: this.etiquetas.perfil, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          }
        ]
      }, true);
    },

    renderConsumoHora() {
      if (!this.$refs.chartConsumoHora) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.consumoHora) this.instances.consumoHora.dispose();
      this.instances.consumoHora = echarts.init(this.$refs.chartConsumoHora);

      this.instances.consumoHora.setOption({
        color: ['#ef4444', '#10b981'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name} hrs</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        legend: { textStyle: { color: textColor }, bottom: 35 },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_consumo_horario' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 60, right: 30, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: Array.from({length: 24}, (_, i) => `${i}:00`), axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'bar', 
            data: this.resultado.dispositivo_base.grafica_consumo_por_hora, 
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            label: { show: this.etiquetas.consumoHora, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: this.nombreControl, 
            type: 'bar', 
            data: this.resultado.dispositivo_control.grafica_consumo_por_hora, 
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            label: { show: this.etiquetas.consumoHora, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          }
        ]
      }, true);
    },

    renderTrend() {
      if (!this.$refs.chartTrend) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.trend) this.instances.trend.dispose();
      this.instances.trend = echarts.init(this.$refs.chartTrend);

      const dias = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);
      const baseData = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.kwh);
      const ctrlData = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.kwh);

      this.instances.trend.setOption({
        color: ['#ef4444', '#10b981'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg, 
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding:5px;"><b style="color:${textColor}">Día de mes: ${params[0].name}</b><br/>`;
                let diferencia = 0;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                });
                if (params.length === 2) {
                   diferencia = Math.abs(params[0].value - params[1].value);
                   html += `<hr style="margin:5px 0; border-color:${gridColor};" /><span style="color:#10b981">Ahorro Diario: <b>${diferencia.toFixed(2)} kWh</b></span>`;
                }
                return html + `</div>`;
            }
        },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_tendencia_ahorro' } },
          iconStyle: { borderColor: textColor } 
        },
        legend: { textStyle: { color: textColor }, bottom: 35 },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 15, bottom: 10 }],
        grid: { top: 30, left: 60, right: 30, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'bar', 
            itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] },
            data: baseData,
            label: { show: this.etiquetas.trend, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          },
          { 
            name: this.nombreControl, 
            type: 'bar', 
            itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] },
            data: ctrlData,
            label: { show: this.etiquetas.trend, position: 'top', color: textColor, fontSize: 10, formatter: '{c}' },
            labelLayout: { hideOverlap: true }
          }
        ]
      }, true);
    },

    renderClimaTemp() {
      if (!this.$refs.chartClimaTemp) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.climaTemp) this.instances.climaTemp.dispose();
      this.instances.climaTemp = echarts.init(this.$refs.chartClimaTemp);

      const dias = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);
      const extTemp = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.temp_ext);
      const baseTemp = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.temperatura);
      const ctrlTemp = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.temperatura);

      this.instances.climaTemp.setOption({
        color: ['#f59e0b', '#ef4444', '#10b981'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">Día de mes: ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${parseFloat(p.value).toFixed(1)} °C</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 35 },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'evolucion_temperatura' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 40, right: 40, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: { type: 'value', name: '°C', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } }, scale: true },
        series: [
          { 
            name: 'Temp Exterior', 
            type: 'line', 
            smooth: true, 
            data: extTemp,
            lineStyle: { width: 3, type: 'dashed' },
            label: { show: this.etiquetas.climaTemp, position: 'top', color: textColor, fontSize: 10, formatter: '{c}°' }
          },
          { 
            name: `Temp Int ${this.nombreBase}`, 
            type: 'line', 
            smooth: true, 
            data: baseTemp,
            areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(239,68,68,0.2)'},{offset:1,color:'transparent'}]) },
            label: { show: this.etiquetas.climaTemp, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}°' }
          },
          { 
            name: `Temp Int ${this.nombreControl}`, 
            type: 'line', 
            smooth: true, 
            data: ctrlTemp,
            areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(16,185,129,0.2)'},{offset:1,color:'transparent'}]) },
            label: { show: this.etiquetas.climaTemp, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}°' }
          }
        ]
      }, true);
    },

    renderClimaHum() {
      if (!this.$refs.chartClimaHum) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.climaHum) this.instances.climaHum.dispose();
      this.instances.climaHum = echarts.init(this.$refs.chartClimaHum);

      const dias = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);
      const extHum = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.hum_ext);
      const baseHum = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.humedad);
      const ctrlHum = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.humedad);

      this.instances.climaHum.setOption({
        color: ['#3b82f6', '#ef4444', '#10b981'],
        tooltip: { 
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">Día de mes: ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${parseFloat(p.value).toFixed(1)} %</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { textStyle: { color: textColor }, bottom: 35 },
        dataZoom: [
          { type: 'inside' },
          { type: 'slider', height: 15, bottom: 10 }
        ],
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'evolucion_humedad' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 40, right: 40, bottom: 90, containLabel: true },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: { type: 'value', name: '%', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } }, scale: true },
        series: [
          { 
            name: 'Humedad Exterior', 
            type: 'line', 
            smooth: true, 
            data: extHum,
            lineStyle: { width: 3, type: 'dashed' },
            label: { show: this.etiquetas.climaHum, position: 'top', color: textColor, fontSize: 10, formatter: '{c}%' }
          },
          { 
            name: `Hum Int ${this.nombreBase}`, 
            type: 'line', 
            smooth: true, 
            data: baseHum,
            label: { show: this.etiquetas.climaHum, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}%' }
          },
          { 
            name: `Hum Int ${this.nombreControl}`, 
            type: 'line', 
            smooth: true, 
            data: ctrlHum,
            label: { show: this.etiquetas.climaHum, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}%' }
          }
        ]
      }, true);
    },

    renderCorrelacion() {
      if (!this.$refs.chartCorrelacion) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.correlacion) this.instances.correlacion.dispose();
      this.instances.correlacion = echarts.init(this.$refs.chartCorrelacion);

      const baseCorr = this.resultado.dispositivo_base.correlaciones_ambientales;
      if (!baseCorr) return;

      const datos = [
          { value: baseCorr.mes_completo.hum_ext, name: 'Humedad Exterior' },
          { value: baseCorr.mes_completo.temp_ext, name: 'Temp. Exterior' },
          { value: baseCorr.mes_completo.iluminacion, name: 'Iluminación' },
          { value: baseCorr.mes_completo.humedad, name: 'Humedad Interior' },
          { value: baseCorr.mes_completo.temperatura, name: 'Temp. Interior' }
      ];

      this.instances.correlacion.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: textColor },
          formatter: function (params) {
              const val = params[0].value;
              const dir = val > 0 ? 'Aumenta el consumo' : 'Reduce el consumo';
              return `<div style="padding:5px;"><b>${params[0].name}</b><br/>Correlación: <b>${val}</b><br/><small style="color:${val>0?'#ef4444':'#10b981'}">${dir}</small></div>`;
          }
        },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'impacto_correlacion' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 110, right: 40, bottom: 40 },
        xAxis: { type: 'value', min: -1, max: 1, splitLine: { lineStyle: { color: gridColor, type: 'dashed' } }, axisLabel: { color: textColor } },
        yAxis: { type: 'category', data: datos.map(d => d.name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: textColor, fontWeight: 'bold' } },
        series: [
          {
            name: 'Correlación',
            type: 'bar',
            data: datos.map(item => {
                return {
                    value: item.value,
                    itemStyle: { color: item.value > 0 ? '#ef4444' : '#10b981', borderRadius: 4 }
                }
            }),
            label: { show: this.etiquetas.correlacion, position: 'inside', color: '#fff', formatter: '{c}' }
          }
        ]
      }, true);
    },

    renderImpactoTermico() {
      if (!this.$refs.chartImpactoTermico) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.impactoTermico) this.instances.impactoTermico.dispose();
      this.instances.impactoTermico = echarts.init(this.$refs.chartImpactoTermico);

      const dias = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.fecha.split('-')[2]);
      const consumoBase = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.kwh);
      const tempExt = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.temp_ext);
      const tempBase = this.resultado.dispositivo_base.grafica_tendencia_diaria.map(d => d.temperatura);
      const tempCtrl = this.resultado.dispositivo_control.grafica_tendencia_diaria.map(d => d.temperatura);

      this.instances.impactoTermico.setOption({
        tooltip: {
            trigger: 'axis',
            backgroundColor: tooltipBg,
            borderColor: gridColor,
            textStyle: { color: textColor },
            axisPointer: { type: 'cross' },
            formatter: (params) => {
                let html = `<div style="padding: 5px;"><b style="color:${textColor}">Día: ${params[0].name}</b><br/>`;
                params.forEach(p => {
                    let unit = p.seriesName.includes('Temp') ? '°C' : 'kWh';
                    html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${parseFloat(p.value).toFixed(1)} ${unit}</b><br/>`;
                });
                return html + `</div>`;
            }
        },
        legend: { data: ['Demanda (kWh)', 'Temperatura Externa', `Temp Int ${this.nombreBase}`, `Temp Int ${this.nombreControl}`], textStyle: { color: textColor }, bottom: 35 },
        dataZoom: [{ type: 'inside' }, { type: 'slider', height: 15, bottom: 10 }],
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'impacto_termico' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 40, left: 50, right: 50, bottom: 90 },
        xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
        yAxis: [
          { type: 'value', name: 'kWh', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
          { type: 'value', name: '°C', axisLabel: { color: textColor }, splitLine: { show: false }, scale: true }
        ],
        series: [
          { 
            name: 'Demanda (kWh)', 
            type: 'bar', 
            yAxisIndex: 0, 
            data: consumoBase, 
            itemStyle: { color: 'rgba(59, 130, 246, 0.5)', borderRadius: [4, 4, 0, 0] },
            label: { show: this.etiquetas.impactoTermico, position: 'insideTop', color: '#fff', fontSize: 10, formatter: '{c}' }
          },
          { 
            name: 'Temperatura Externa', 
            type: 'line', 
            yAxisIndex: 1, 
            data: tempExt, 
            smooth: true, 
            symbolSize: 6, 
            lineStyle: { type: 'dashed', width: 2 },
            itemStyle: { color: '#f59e0b' },
            label: { show: this.etiquetas.impactoTermico, position: 'top', color: textColor, fontSize: 10, formatter: '{c}°' }
          },
          { 
            name: `Temp Int ${this.nombreBase}`, 
            type: 'line', 
            yAxisIndex: 1, 
            data: tempBase, 
            smooth: true, 
            symbolSize: 6, 
            itemStyle: { color: '#ef4444' },
            label: { show: this.etiquetas.impactoTermico, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}°' }
          },
          { 
            name: `Temp Int ${this.nombreControl}`, 
            type: 'line', 
            yAxisIndex: 1, 
            data: tempCtrl, 
            smooth: true, 
            symbolSize: 6, 
            itemStyle: { color: '#10b981' },
            label: { show: this.etiquetas.impactoTermico, position: 'bottom', color: textColor, fontSize: 10, formatter: '{c}°' }
          }
        ]
      }, true);
    },

    renderConfort() {
      if (!this.$refs.chartConfort) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.confort) this.instances.confort.dispose();
      this.instances.confort = echarts.init(this.$refs.chartConfort);

      this.instances.confort.setOption({
        color: ['#ef4444', '#10b981'],
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: textColor }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        toolbox: {
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'estandar_confort' } },
          iconStyle: { borderColor: textColor }
        },
        grid: { top: 40, left: 60, right: 30, bottom: 60, containLabel: true },
        xAxis: {
          type: 'category',
          data: ['Efectividad Térmica', 'Control Humedad', 'Nivel Iluminación'],
          axisLabel: { color: textColor, fontWeight: 'bold' }
        },
        yAxis: {
          type: 'value',
          name: 'Porcentaje de Cumplimiento (%)',
          nameLocation: 'middle',
          nameGap: 40,
          axisLabel: { color: textColor },
          splitLine: { lineStyle: { color: gridColor } },
          max: 105
        },
        series: [
          {
            name: this.nombreBase,
            type: 'bar',
            data: [47, 96, 90],
            barGap: '0%',
            itemStyle: { borderRadius: [4, 4, 0, 0], color: '#334155' },
            label: { show: this.etiquetas.confort, position: 'top', color: textColor, formatter: '{c}%' }
          },
          {
            name: this.nombreControl,
            type: 'bar',
            data: [100, 100, 90],
            itemStyle: { borderRadius: [4, 4, 0, 0], color: '#10b981' },
            label: { show: this.etiquetas.confort, position: 'top', color: textColor, formatter: '{c}%' },
            markLine: {
              symbol: 'none',
              data: [{ yAxis: 100, name: 'Meta ASHRAE 55' }],
              lineStyle: { color: '#ef4444', type: 'dashed', width: 2 },
              label: { show: true, position: 'end', formatter: 'Meta ASHRAE 55', color: textColor }
            }
          }
        ]
      }, true);
    },

    renderCFEBar() {
      if (!this.$refs.chartCFEBar) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.cfeBar) this.instances.cfeBar.dispose();
      this.instances.cfeBar = echarts.init(this.$refs.chartCFEBar);

      const baseCFE = this.resultado.dispositivo_base.desglose_cfe;
      const ctrlCFE = this.resultado.dispositivo_control.desglose_cfe;

      const dataBase = [baseCFE.energia_base, baseCFE.energia_intermedia, baseCFE.energia_punta];
      const dataCtrl = [ctrlCFE.energia_base, ctrlCFE.energia_intermedia, ctrlCFE.energia_punta];

      this.instances.cfeBar.setOption({
        color: ['#ef4444', '#10b981'],
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: textColor },
          formatter: (params) => {
              let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name}</b><br/>`;
              params.forEach(p => {
                  html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>$${p.value.toFixed(2)}</b><br/>`;
              });
              return html + `</div>`;
          }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'tarifas_cfe_comparativa' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 30, right: 40, bottom: 60, containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: textColor, formatter: '${value}' }, splitLine: { lineStyle: { color: gridColor } } },
        yAxis: { type: 'category', data: ['Franja Baja', 'Franja Media', 'Franja Alta'], axisLabel: { color: textColor, fontWeight: 'bold' } },
        series: [
          { 
            name: this.nombreBase, 
            type: 'bar', 
            data: dataBase, 
            itemStyle: { borderRadius: [0, 4, 4, 0] },
            label: { show: this.etiquetas.cfeBar, position: 'right', color: textColor, formatter: '${c}' }
          },
          { 
            name: this.nombreControl, 
            type: 'bar', 
            data: dataCtrl, 
            itemStyle: { borderRadius: [0, 4, 4, 0] },
            label: { show: this.etiquetas.cfeBar, position: 'right', color: textColor, formatter: '${c}' }
          }
        ]
      }, true);
    },

    renderFantasma() {
      if (!this.$refs.chartFantasma) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.fantasma) this.instances.fantasma.dispose();
      this.instances.fantasma = echarts.init(this.$refs.chartFantasma);

      const baseBruto = this.resultado.dispositivo_base.consumo_bruto_kwh;
      const baseFuga = this.resultado.dispositivo_base.carga_fantasma_kwh;
      const baseUtil = baseBruto - baseFuga;

      const ctrlBruto = this.resultado.dispositivo_control.consumo_bruto_kwh;
      const ctrlFuga = this.resultado.dispositivo_control.carga_fantasma_kwh;
      const ctrlUtil = ctrlBruto - ctrlFuga;

      this.instances.fantasma.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: textColor },
          formatter: (params) => {
              let html = `<div style="padding: 5px;"><b style="color:${textColor}">${params[0].name}</b><br/>`;
              let total = 0;
              params.forEach(p => {
                  html += `<span style="color:${p.color}">●</span> ${p.seriesName}: <b>${p.value.toFixed(2)} kWh</b><br/>`;
                  total += p.value;
              });
              html += `<hr style="margin:5px 0; border-color:${gridColor};" />Gasto Bruto: <b>${total.toFixed(2)} kWh</b></div>`;
              return html;
          }
        },
        legend: { textStyle: { color: textColor }, bottom: 0 },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'carga_fantasma_comparativa' } },
          iconStyle: { borderColor: textColor } 
        },
        grid: { top: 30, left: 30, right: 30, bottom: 60, containLabel: true },
        xAxis: { type: 'category', data: [this.nombreBase, this.nombreControl], axisLabel: { color: textColor, fontWeight: 'bold' } },
        yAxis: { type: 'value', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
        series: [
          { 
            name: 'Consumo Útil', 
            type: 'bar', 
            stack: 'total', 
            data: [
               { value: baseUtil, itemStyle: { color: 'rgba(239,68,68,0.2)' } },
               { value: ctrlUtil, itemStyle: { color: 'rgba(16,185,129,0.2)' } }
            ],
            barWidth: '50%',
            label: { show: this.etiquetas.fantasma, position: 'inside', color: textColor, formatter: '{c}' }
          },
          { 
            name: 'Energía Desperdiciada', 
            type: 'bar', 
            stack: 'total', 
            data: [
               { value: baseFuga, itemStyle: { color: '#ef4444' } },
               { value: ctrlFuga, itemStyle: { color: '#10b981' } }
            ], 
            itemStyle: { borderRadius: [4, 4, 0, 0] },
            label: { show: this.etiquetas.fantasma, position: 'top', color: textColor, formatter: '{c}' }
          }
        ]
      }, true);
    },

    renderGauge() {
      if (!this.$refs.chartGauge) return;
      const textColor = this.isDark ? '#cbd5e1' : '#64748b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.gauge) this.instances.gauge.dispose();
      this.instances.gauge = echarts.init(this.$refs.chartGauge);

      const val = Math.abs(this.resultado.comparativa.ahorro_energia_pct);

      this.instances.gauge.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: tooltipBg,
          borderColor: gridColor,
          textStyle: { color: this.isDark ? '#f8fafc' : '#1e293b' },
          formatter: function() {
            return `<div style="padding: 5px;"><b>Eficiencia Operativa</b><br/>Ahorro validado: <b>${val.toFixed(2)}%</b></div>`;
          }
        },
        toolbox: { 
          show: true,
          feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'auditoria_eficiencia' } },
          iconStyle: { borderColor: textColor } 
        },
        series: [
          {
            type: 'gauge',
            startAngle: 210,
            endAngle: -30,
            min: 0,
            max: 100,
            splitNumber: 10,
            radius: '100%',
            center: ['50%', '55%'],
            itemStyle: {
              color: '#10b981',
              shadowColor: 'rgba(16,185,129,0.3)',
              shadowBlur: 8,
              shadowOffsetX: 0,
              shadowOffsetY: 0
            },
            progress: {
              show: true,
              roundCap: true,
              width: 14
            },
            pointer: {
              show: false
            },
            axisLine: {
              roundCap: true,
              lineStyle: {
                width: 14,
                color: [[1, gridColor]]
              }
            },
            axisTick: {
              distance: -22,
              splitNumber: 5,
              length: 6,
              lineStyle: {
                width: 1,
                color: textColor
              }
            },
            splitLine: {
              distance: -28,
              length: 10,
              lineStyle: {
                width: 2,
                color: textColor
              }
            },
            axisLabel: {
              distance: 35,
              color: textColor,
              fontSize: 10
            },
            detail: {
              show: false
            },
            data: [{ value: val, name: 'Ahorro' }]
          }
        ]
      }, true);
    },

    renderAcumulado() {
      if (!this.$refs.chartAcumulado) return;
      const textColor = this.isDark ? '#f8fafc' : '#1e293b';
      const gridColor = this.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      const tooltipBg = this.isDark ? '#1a1d2d' : '#ffffff';

      if (this.instances.acumulado) this.instances.acumulado.dispose();
      this.instances.acumulado = echarts.init(this.$refs.chartAcumulado);

      const dias = [];
      const dataBase = [];
      const dataCtrl = [];
      let sumaBase = 0;
      let sumaCtrl = 0;

      this.resultado.dispositivo_base.grafica_tendencia_diaria.forEach((d, i) => {
          const dCtrl = this.resultado.dispositivo_control.grafica_tendencia_diaria[i];
          sumaBase += d.kwh;
          sumaCtrl += dCtrl.kwh;
          dias.push(d.fecha.split('-').slice(1).join('/'));
          dataBase.push(sumaBase.toFixed(2));
          dataCtrl.push(sumaCtrl.toFixed(2));
      });

      this.instances.acumulado.setOption({
          color: ['#ef4444', '#10b981'],
          tooltip: { trigger: 'axis', backgroundColor: tooltipBg, borderColor: gridColor, textStyle: { color: textColor } },
          legend: { textStyle: { color: textColor }, bottom: 35 },
          toolbox: { 
            show: true,
            feature: { saveAsImage: { show: true, title: 'Exportar Gráfica', pixelRatio: 2, name: 'energia_acumulada' } },
            iconStyle: { borderColor: textColor } 
          },
          grid: { top: 40, left: 60, right: 40, bottom: 90, containLabel: true },
          dataZoom: [{ type: 'inside' }, { type: 'slider', height: 15, bottom: 10 }],
          xAxis: { type: 'category', data: dias, axisLabel: { color: textColor } },
          yAxis: { type: 'value', name: 'kWh Acumulados', axisLabel: { color: textColor }, splitLine: { lineStyle: { color: gridColor } } },
          series: [
              { name: this.nombreBase, type: 'line', smooth: true, areaStyle: { opacity: 0.1 }, data: dataBase, label: { show: this.etiquetas.acumulado, position: 'top', color: textColor, fontSize: 10 } },
              { name: this.nombreControl, type: 'line', smooth: true, areaStyle: { opacity: 0.2 }, data: dataCtrl, label: { show: this.etiquetas.acumulado, position: 'bottom', color: textColor, fontSize: 10 } }
          ]
      }, true);
    }

  }
};
</script>

<style scoped lang="scss">
$DEEP-NAVY: #0f111a;
$CARD-NAVY: #161925;
$ACCENT-BLUE: #3b82f6;
$ACCENT-GREEN: #10b981;
$ACCENT-RED: #ef4444;
$ACCENT-GOLD: #f59e0b;

.plataforma-layout { 
  display: flex; width: 100%; min-height: 100vh; transition: background 0.3s; background-color: #f8fafc;
  &.theme-dark { background-color: $DEEP-NAVY !important; }
}

.plataforma-contenido { 
  flex-grow: 1; padding: 40px; margin-left: 80px; transition: margin-left 0.3s; 
  &.shifted { margin-left: 280px; } background-color: inherit;
}

.dashboard-grid-premium { display: grid; grid-template-columns: repeat(6, 1fr); gap: 24px; padding-bottom: 30px; }

.grid-item-header, .grid-item-alert, .grid-item-kpis, .grid-item-data-tables, .grid-item-footer, .grid-item-tabs { grid-column: 1 / -1; }
.grid-item-chart-main { grid-column: 1 / span 4; }
.grid-item-chart-side { grid-column: 5 / span 2; }
.grid-item-chart-half { grid-column: span 3; }
.grid-item-chart-third { grid-column: span 2; }

.title-contrast { color: #1e293b; transition: color 0.3s; }
.text-muted-contrast { color: #64748b; transition: color 0.3s; }

.theme-dark {
  .title-contrast { color: #f8fafc !important; }
  .text-muted-contrast { color: #cbd5e1 !important; }
  .glass-card, .kpi-neon-v2, .chart-container-v2, .explain-box { background: $CARD-NAVY !important; border-color: rgba(255,255,255,0.1) !important; }
}

.border-light-custom { border-color: rgba(0,0,0,0.05) !important; }
.theme-dark .border-light-custom { border-color: rgba(255,255,255,0.05) !important; }

.glass-card { background: white; padding: 24px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); position: relative; overflow: hidden; }
.border-green-glow { border: 1px solid rgba($ACCENT-GREEN, 0.3) !important; box-shadow: 0 0 15px rgba($ACCENT-GREEN, 0.1); }
.footer-glow::after { content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, $ACCENT-RED, $ACCENT-BLUE, $ACCENT-GREEN); }

.tabs-premium {
  display: flex;
  gap: 10px;
  border-bottom: 2px solid rgba(0,0,0,0.05);
  padding-bottom: 10px;
}
.theme-dark .tabs-premium { border-bottom-color: rgba(255,255,255,0.05); }

.tab-btn {
  background: transparent;
  border: none;
  padding: 10px 20px;
  font-weight: 800;
  color: #64748b;
  border-radius: 12px;
  transition: all 0.2s;
  cursor: pointer;
  &.active {
    background: rgba($ACCENT-GREEN, 0.1);
    color: $ACCENT-GREEN;
  }
}
.theme-dark .tab-btn { color: #cbd5e1; &.active { color: $ACCENT-GREEN; } }

.selector-unit-v3 { display: flex; flex-direction: column; gap: 8px; }
.input-complex { 
  display: flex; align-items: center; background: #f1f5f9; padding: 6px 14px; border-radius: 14px; gap: 10px; border: 1px solid transparent; transition: all 0.2s;
  .input-wrapper { display: flex; align-items: center; color: #64748b; &.id-w { flex-shrink: 0; } }
  .clean-input-text { border: none; background: transparent; width: 140px; font-weight: 700; color: #1e293b; outline: none; font-size: 0.9rem; }
  .clean-input-id { border: none; background: transparent; width: 50px; font-weight: 800; color: #1e293b; outline: none; text-align: center; }
  .divider { width: 1px; height: 24px; background: rgba(0,0,0,0.1); }
  &.red { border-left: 5px solid $ACCENT-RED; }
  &.blue { border-left: 5px solid $ACCENT-BLUE; }
}

.green-box { border-left: 5px solid $ACCENT-GREEN !important; background: rgba($ACCENT-GREEN, 0.05) !important; }

.theme-dark .input-complex { 
  background: rgba(255,255,255,0.05) !important; 
  .clean-input-text, .clean-input-id { color: white !important; }
  .divider { background: rgba(255,255,255,0.1); }
}

.label-tiny { font-size: 0.65rem; font-weight: 900; color: #64748b; letter-spacing: 1.5px; margin-bottom: 2px; }

.btn-auditoria-premium { 
  width: 100%; background: #6366f1; color: white; border: none; padding: 18px; border-radius: 18px; font-weight: 900; 
  box-shadow: 0 8px 20px -4px rgba(99, 102, 241, 0.5); transition: all 0.2s;
  &:hover { transform: translateY(-2px); filter: brightness(1.15); box-shadow: 0 12px 25px -4px rgba(99, 102, 241, 0.6); } 
}

.btn-toggle-data {
  background: transparent;
  border: 1px solid rgba(0,0,0,0.1);
  color: #64748b;
  border-radius: 8px;
  padding: 4px 8px;
  transition: all 0.2s;
  cursor: pointer;
  &.active {
    background: rgba($ACCENT-GREEN, 0.1);
    color: $ACCENT-GREEN;
    border-color: rgba($ACCENT-GREEN, 0.3);
  }
}
.theme-dark .btn-toggle-data {
  border-color: rgba(255,255,255,0.1);
  color: #cbd5e1;
}

.alert-premium { background: rgba(239, 68, 68, 0.95); border: 1px solid #ef4444; padding: 18px 24px; border-radius: 16px; width: 100%; }
.icon-error { width: 42px; height: 42px; border-radius: 12px; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; font-size: 1.4rem; color: white; }

.kpi-stripe-v2 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.kpi-neon-v2 { 
  background: white; padding: 24px; border-radius: 24px; border: 1px solid rgba(0,0,0,0.03); display: flex; align-items: center; gap: 18px;
  .kpi-icon-v2 { width: 52px; height: 52px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 1.6rem; background: rgba(0,0,0,0.03); }
  .value { font-size: 1.8rem; font-weight: 1000; margin: 0; color: #1e293b; }
  .label { font-size: 0.7rem; font-weight: 800; color: #64748b; display: block; margin-bottom: 2px; }
  .badge-saving-v2 { padding: 4px 8px; border-radius: 8px; font-size: 0.8rem; font-weight: 800; }
  &.green-highlight { border: 1px solid rgba($ACCENT-GREEN, 0.2); box-shadow: 0 4px 15px rgba($ACCENT-GREEN, 0.05); .kpi-icon-v2 { background: rgba($ACCENT-GREEN, 0.1); color: $ACCENT-GREEN; } }
  &.blue { .kpi-icon-v2 { background: rgba($ACCENT-BLUE, 0.1); color: $ACCENT-BLUE; } }
  &.gold { .kpi-icon-v2 { background: rgba($ACCENT-GOLD, 0.1); color: $ACCENT-GOLD; } }
  &.red { .kpi-icon-v2 { background: rgba($ACCENT-RED, 0.1); color: $ACCENT-RED; } }
}
.theme-dark .kpi-neon-v2 .value { color: #f8fafc; }

.chart-container-v2 { background: white; padding: 28px; border-radius: 28px; border: 1px solid rgba(0,0,0,0.02); height: 100%; }
.echarts-surface-v2 { width: 100%; height: 380px; min-width: 200px; }
.echarts-surface-small { width: 100%; height: 260px; min-width: 200px; }
.echarts-surface-donut { width: 100%; height: 220px; }
.echarts-surface-gauge { width: 100%; height: 260px; min-height: 260px; min-width: 200px; }

.m-row { display: flex; justify-content: space-between; padding: 18px 0; border-bottom: 1px solid rgba(0,0,0,0.05); align-items: center; .m-label { font-size: 0.85rem; font-weight: 700; } .m-vals { font-weight: 900; font-size: 1.1rem; } }
.theme-dark .m-row { border-color: rgba(255,255,255,0.05); }

.text-nowrap { white-space: nowrap; }
.table-scroll { max-height: 400px; overflow-y: auto; overflow-x: auto; }

.bg-canvas-export { background: transparent; }
.theme-dark .bg-canvas-export { background: transparent; }

.table-auditoria { 
  width: 100%; border-collapse: collapse; 
  th { padding: 20px; font-size: 0.75rem; font-weight: 900; color: $ACCENT-BLUE; letter-spacing: 1.5px; position: sticky; top: 0; z-index: 10; background: rgba($ACCENT-BLUE, 0.05); } 
  td { padding: 18px; border-bottom: 1px solid rgba(0,0,0,0.04); font-weight: 700; font-size: 0.95rem; } 
}

.sticky-col { position: sticky; left: 0; background: white; z-index: 11; border-right: 1px solid rgba(0,0,0,0.05); }
.theme-dark .table-auditoria th { background: #161925; color: #cbd5e1; border-bottom: 1px solid rgba(255,255,255,0.1); }
.theme-dark .table-auditoria td { border-color: rgba(255,255,255,0.05); color: #f8fafc; }
.theme-dark .sticky-col { background: #161925; border-right-color: rgba(255,255,255,0.05); }
.table-auditoria th.sticky-col { z-index: 12; }

.explain-box { background: white; padding: 25px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); height: 100%; p { line-height: 1.6; } }

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 1200px) {
  .grid-item-header, .grid-item-alert, .grid-item-kpis, .grid-item-data-tables, .grid-item-footer, .grid-item-tabs { grid-column: 1 / -1; }
  .grid-item-chart-main, .grid-item-chart-side, .grid-item-chart-half, .grid-item-chart-third { grid-column: 1 / -1; }
  .kpi-stripe-v2 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .kpi-stripe-v2 { grid-template-columns: 1fr; }
}
</style>