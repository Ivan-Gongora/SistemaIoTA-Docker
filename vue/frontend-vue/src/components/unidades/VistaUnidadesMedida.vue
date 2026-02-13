<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <BarraLateralPlataforma :is-open="isSidebarOpen" />
    
    <div class="plataforma-contenido" :class="{ 'shifted': isSidebarOpen }">
      
      <EncabezadoPlataforma
        titulo="Unidades de Medida"
        subtitulo="Gestión de estándares de medición para sensores"
        @toggle-sidebar="toggleSidebar"
        :is-sidebar-open="isSidebarOpen"
      />

      <div class="unidades-contenido">
        
        <div v-if="loading" class="alert-info">Cargando unidades...</div>
        <div v-else-if="error" class="alert-error">{{ error }}</div>
        
        <div v-else>
          <div class="unidades-header">
            <h3>Total de Unidades: {{ filteredUnidades.length }}</h3>
            <div class="search-and-actions">
              <input
                type="text"
                v-model="searchQuery"
                class="form-control-search"
                placeholder="Buscar por nombre, símbolo o magnitud..."
              >
              <button @click="openCreateModal" class="btn-primary-action">
                <i class="bi bi-plus-circle-fill"></i> Nueva Unidad
              </button>
            </div>
          </div>

          <div class="lista-interactiva-container">
            
            <div class="lista-header">
              <div class="col-id">ID</div>
              <div class="col-nombre">Nombre</div>
              <div class="col-simbolo">Símbolo</div>
              <div class="col-magnitud">Tipo de Magnitud</div>
              <div class="col-descripcion">Descripción</div>
              <div class="col-acciones">Acciones</div>
            </div>

            <div class="lista-body">
              <div 
                v-for="unidad in filteredUnidades" 
                :key="unidad.id" 
                class="lista-fila"
              >
                <div class="col-id">{{ unidad.id }}</div>
                <div class="col-nombre">{{ unidad.nombre }}</div>
                <div class="col-simbolo">
                  <span class="simbolo-badge">{{ unidad.simbolo }}</span>
                </div>
                <div class="col-magnitud">{{ unidad.magnitud_tipo }}</div>
                <div class="col-descripcion">{{ unidad.descripcion || 'Sin descripción.' }}</div>
                
                <div class="col-acciones">
                  <button @click="openEditModal(unidad)" class="btn-action btn-edit" title="Modificar">
                    <i class="bi bi-pencil"></i>
                  </button>
                </div>
              </div>
            </div>

          </div>
          
          <div v-if="filteredUnidades.length === 0 && unidades.length > 0" class="alert-empty-data">
            No se encontraron unidades que coincidan con "{{ searchQuery }}".
          </div>
          <div v-if="unidades.length === 0" class="alert-empty-data">
            No hay unidades de medida registradas.
          </div>
        </div>
      </div>
    </div>
    
    <ModalUnidadMedida
      v-if="mostrarModalCrear"
      :is-dark="isDark"
      :modo-edicion="false"
      @unidad-guardada="handleUnidadGuardada"
      @close="closeCreateModal"
    />
    <ModalUnidadMedida
      v-if="mostrarModalEditar"
      :is-dark="isDark"
      :modo-edicion="true"
      :unidad-data="unidadSeleccionada"
      @unidad-guardada="handleUnidadGuardada"
      @close="closeEditModal"
    />
  </div>
</template>

<script>
import BarraLateralPlataforma from '../plataforma/BarraLateralPlataforma.vue';
import EncabezadoPlataforma from '../plataforma/EncabezadoPlataforma.vue';
import ModalUnidadMedida from './ModalUnidadMedida.vue'; 
// 🚨 NOTA: Si usas un modal de eliminación, impórtalo aquí.

// const API_BASE_URL = 'http://127.0.0.1:8001';

export default {
    name: 'VistaUnidadesMedida',
    components: {
        BarraLateralPlataforma,
        EncabezadoPlataforma,
        ModalUnidadMedida,
        // ... otros modales
    },
    data() {
        return {
            isDark: false,
            isSidebarOpen: true,
            loading: true,
            error: null,
            unidades: [], 
            
            mostrarModalCrear: false,
            mostrarModalEditar: false,
            unidadSeleccionada: null,
            // Estado para la búsqueda
            searchQuery: '',
        };
    },
    mounted() {
        this.cargarUnidades();
        this.detectarTemaSistema();
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
        }
    },
    computed: {
        // 🚨 NUEVO: Propiedad computada para filtrar la lista
        filteredUnidades() {
            if (!this.searchQuery) {
                return this.unidades; // Si no hay búsqueda, devuelve la lista completa
            }
            
            const lowerQuery = this.searchQuery.toLowerCase();
            
            return this.unidades.filter(unidad => {
                // Busca en nombre, simbolo o magnitud
                return (
                    unidad.nombre.toLowerCase().includes(lowerQuery) ||
                    unidad.simbolo.toLowerCase().includes(lowerQuery) ||
                    (unidad.magnitud_tipo && unidad.magnitud_tipo.toLowerCase().includes(lowerQuery))
                );
            });
        }
    },
    beforeUnmount() {
         if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
        } },
    methods: {
        // -----------------------------------------------------
        // 🚨 CONSUMO DE API (Sin permisos complejos)
        // -----------------------------------------------------
        async cargarUnidades() {
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');
            
            if (!token) { this.$router.push('/'); return; }

            try {
                const response = await fetch(`${API_BASE_URL}/api/unidades`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (!response.ok) {
                    // Si el 403 ocurre aquí, significa que el backend SÍ tiene el problema de permisos que pusimos en espera
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Fallo al obtener unidades.');
                }
                
                this.unidades = await response.json();
                
            } catch (err) {
                this.error = err.message || 'Error de conexión al obtener unidades.';
            } finally {
                this.loading = false;
            }
        },
        
        // -----------------------------------------------------
        // MANEJO DE MODALES Y ACCIONES (CRUD)
        // -----------------------------------------------------
        
        // Creación
        openCreateModal() { this.mostrarModalCrear = true; },
        closeCreateModal() { this.mostrarModalCrear = false; },
        
        // Edición
        openEditModal(unidad) {
            this.unidadSeleccionada = unidad;
            this.mostrarModalEditar = true;
        },
        closeEditModal() {
            this.mostrarModalEditar = false;
            this.unidadSeleccionada = null;
        },
        
        // Recarga después de Crear/Editar
        handleUnidadGuardada() {
            this.closeCreateModal();
            this.closeEditModal();
            this.cargarUnidades(); // 🚨 Sincroniza con el backend
        },
     
        
        // -----------------------------------------------------
        // LÓGICA DE LAYOUT
        // -----------------------------------------------------
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

.unidades-contenido {
    padding: 20px 40px 40px 40px;
}

// ----------------------------------------
// HEADER (Buscador y Botón)
// ----------------------------------------
.unidades-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    h3 { font-size: 1.4rem; font-weight: 600; }
    .btn-primary-action {
        background-color: $SUCCESS-COLOR;
        color: white;
        border: none;
        padding: 10px 15px;
        border-radius: 8px;
        font-weight: 600;
        i { margin-right: 5px; }
    }
    .search-and-actions {
        display: flex;
        gap: 15px;
        align-items: center;
    }
}
.form-control-search {
    padding: 10px 15px;
    border-radius: 8px;
    border: 1px solid #ddd;
    min-width: 300px;
    font-size: 0.95rem;
}

// ----------------------------------------
// ESTILOS: LISTA INTERACTIVA
// ----------------------------------------
.lista-interactiva-container {
    background-color: $SUBTLE-BG-LIGHT;
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    overflow: hidden;
    border: 1px solid #eee;
}

// Definición de las columnas (Grid)
.lista-header, .lista-fila {
    display: grid;
    // 6 columnas: ID, Nombre, Símbolo, Magnitud, Descripción, Acciones
    grid-template-columns: 0.5fr 1fr 1fr 1fr 1.5fr 0.5fr; 
    align-items: center;
    padding: 12px 20px;
    gap: 15px;
}

// --- Encabezado ---
.lista-header {
    background-color: $BLUE-MIDNIGHT; // Encabezado oscuro siempre
    color: $GRAY-COLD;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .col-acciones {
        justify-self: end; // Alinea "Acciones" a la derecha
    }
}

// --- Filas ---
.lista-fila {
    font-size: 0.95rem;
    border-bottom: 1px solid #eee; // Separador sutil
    transition: background-color 0.2s ease-out;

    // INTERACCIÓN CLAVE: Ocultar botones por defecto
    .col-acciones {
        justify-self: end;
        opacity: 0; // Oculto por defecto
        transition: opacity 0.2s ease-out;
    }

    // INTERACCIÓN CLAVE: Mostrar botones en hover
    &:hover {
        .col-acciones {
            opacity: 1; // Visible en hover
        }
    }
}
.lista-body {
    .lista-fila:last-child {
        border-bottom: none;
    }
}

// --- Columnas ---
.col-id { font-weight: 700; }
.col-nombre { font-weight: 500; }
.col-descripcion { 
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: $GRAY-COLD;
}
.col-magnitud { font-style: italic; }

// --- Badge de Símbolo (Reutilizado) ---
.simbolo-badge {
    font-weight: bold;
    padding: 4px 8px;
    border-radius: 4px;
    background-color: $PRIMARY-PURPLE;
    color: white;
}
.btn-action {
    background: none; border: none;
    color: $GRAY-COLD;
    font-size: 1rem;
    margin-left: 10px;
    &:hover { color: $PRIMARY-PURPLE; }
}


// ----------------------------------------
// TEMAS (REACTIVIDAD Y MODO OSCURO)
// ----------------------------------------

.theme-light {
    background-color: $WHITE-SOFT; 
    color: $DARK-TEXT; 
    .form-control-search {
        background-color: $SUBTLE-BG-LIGHT;
        border-color: #ddd;
        color: $DARK-TEXT;
    }
}

.theme-dark {
    background-color: $DARK-BG-CONTRAST; 
    color: $LIGHT-TEXT;
    
    .plataforma-contenido { background-color: $DARK-BG-CONTRAST; }

    .lista-interactiva-container {
        background-color: $SUBTLE-BG-DARK;
        border-color: rgba($LIGHT-TEXT, 0.1);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }
    
    .lista-fila {
        border-bottom-color: rgba($LIGHT-TEXT, 0.1);
        color: $LIGHT-TEXT;

        // Efecto hover en modo oscuro
        &:hover {
            background-color: rgba($LIGHT-TEXT, 0.05);
        }
    }
    .lista-header {
        background-color: $BLUE-MIDNIGHT; // Mantenemos el header oscuro
    }

    .col-descripcion, .col-magnitud {
        color: $GRAY-COLD;
    }
    .btn-action { color: $GRAY-COLD; }

    .form-control-search {
        background-color: $BLUE-MIDNIGHT; 
        border: 1px solid rgba($LIGHT-TEXT, 0.2); 
        color: $LIGHT-TEXT; 
        &::placeholder { color: $GRAY-COLD; }
    }
}
</style>