<template>
  <div class="plataforma-layout" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <div class="mis-proyectos-contenido">
      
      <!-- HEADER DE LA VISTA -->
      <div class="proyectos-header-view">       
        
        <!-- GRUPO IZQUIERDO: Contador -->
        <div class="left-group">
             <span class="count-total">
                <strong>{{ totalRecords }}</strong> proyectos encontrados
            </span>
        </div>

        <!-- GRUPO DERECHO: Buscador y Botón -->
        <div class="actions-group">
            
            <div class="search-box">
                <i class="bi bi-search search-icon"></i>
                <input 
                    type="text" 
                    v-model="searchQuery" 
                    @input="onSearchInput" 
                    placeholder="Buscar proyectos..." 
                    class="search-input"
                >
            </div>

            <button class="btn-nuevo-proyecto" @click="mostrarModalCrear = true">
                <i class="bi bi-plus-lg icon-space"></i> Nuevo Proyecto
            </button>
            
        </div>
      </div>

      <!-- ESTADOS DE CARGA -->
      <div v-if="error" class="alerta-error">{{ error }}</div>
      
      <div v-else-if="loading" class="alerta-loading">
        <i class="bi bi-arrow-clockwise fa-spin"></i> Cargando proyectos...
      </div>
      
      <!-- GRID DE PROYECTOS -->
     <div v-else-if="proyectos.length > 0" class="proyectos-grid">
  <TarjetaProyecto 
      v-for="proyecto in proyectos" 
      :key="proyecto.id" 
      :proyecto="proyecto" 
      :is-dark="isDark"
      @edit-project="handleEditClick" 
      @confirmar-eliminar="confirmarEliminacion"
      @open-share-modal="openShareModal"
  />
  </div>
      
      <div v-else class="alerta-vacio">
        <i class="bi bi-box-fill"></i> No se encontraron proyectos.
      </div>

      <!-- PAGINACIÓN -->
      <div class="pagination-controls" v-if="totalPages > 1">
        <button 
            class="btn-page" 
            :disabled="page === 1" 
            @click="changePage(page - 1)"
        >
            <i class="bi bi-chevron-left"></i> Anterior
        </button>
        
        <span class="page-info">Página {{ page }} de {{ totalPages }}</span>
        
        <button 
            class="btn-page" 
            :disabled="page === totalPages" 
            @click="changePage(page + 1)"
        >
            Siguiente <i class="bi bi-chevron-right"></i>
        </button>
      </div>

    </div>

    <!-- MODALES -->
    <ModalEliminarProyecto 
        v-if="mostrarModalEliminar" 
        :proyecto-id="proyectoEliminarId" 
        :usuario-id="id_usuario"
        @cancelar="cerrarModalEliminar" 
        @confirmar="eliminar(proyectoEliminarId)" 
         
    />
    
    <ModalEditarProyecto 
        v-if="mostrarModalEditar" 
        :proyecto="proyectoSeleccionado" 
        @updated="handleProyectoActualizado" 
        @close="closeEditModal" 
    />
    
    <ModalProyecto 
        v-if="mostrarModalCrear" 
        @creado="handleProyectoCreado" 
        @cerrar="cerrarModalCrear" 
    />
    
    <ModalCompartir 
        v-if="mostrarModalCompartir" 
        :proyecto-id="proyectoCompartirId" 
        @cerrar="closeShareModal" 
    />
    
  </div>
</template>

<script>
import TarjetaProyecto from './TarjetaProyecto.vue';
import ModalProyecto from './CrearProyecto.vue';
import ModalEliminarProyecto from './ModalEliminar.vue';
import ModalCompartir from './ModalCompartir.vue'; 
import ModalEditarProyecto from './ModalEditarProyecto.vue'; 
import debounce from 'lodash/debounce'; 

// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
    name: 'MisProyectos',
    components: {
        TarjetaProyecto, ModalProyecto, ModalEliminarProyecto, ModalCompartir, ModalEditarProyecto
    },
    props: {
        isDark: { type: Boolean, required: true }
    },
    data() {
        return {
            proyectos: [],
            loading: true,
            error: null,
            
            // Datos de Usuario
            id_usuario: null,
            
            // Estados de Modales
            mostrarModalEliminar: false, proyectoEliminarId: null,
            mostrarModalCrear: false,
            mostrarModalCompartir: false, proyectoCompartirId: null,
            mostrarModalEditar: false, proyectoSeleccionado: null,

            // Paginación y Búsqueda
            searchQuery: '',
            page: 1,
            limit: 9, 
            totalPages: 1,
            totalRecords: 0
        };
    },
    mounted() {
        this.cargarProyectos();
    },
    created() {
        this.debouncedSearch = debounce(() => {
            this.page = 1; 
            this.cargarProyectos();
        }, 500);
    },
    methods: {
        // -----------------------------------------------------------------------
        // LÓGICA DE CARGA (SIDE-LOADING IMPLEMENTADO)
        // -----------------------------------------------------------------------
        onSearchInput() {
            this.debouncedSearch();
        },

        changePage(newPage) {
            if (newPage >= 1 && newPage <= this.totalPages) {
                this.page = newPage;
                this.cargarProyectos();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        },

        async cargarProyectos() {
            this.loading = true;
            this.error = null;
            
            // Obtener usuario del localStorage
            const resultado = JSON.parse(localStorage.getItem('resultado')); 
            const token = localStorage.getItem('accessToken'); 

            if (!token) {
                this.$router.push('/');
                return;
            }
            
            // Fallback seguro si resultado es null
            this.id_usuario = resultado?.usuario?.id;
            if (!this.id_usuario) {
                 this.error = "Error de sesión. Usuario no identificado.";
                 this.loading = false;
                 return;
            }
            
            const params = new URLSearchParams({
                page: this.page,
                limit: this.limit,
                search: this.searchQuery
            });
            
            const url = `${API_BASE_URL}/api/proyectos/usuario/${this.id_usuario}?${params.toString()}`;
            
            try {
                const response = await fetch(url, {
                    method: 'GET',
                    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
                });

                if (response.status === 401) {
                    this.$router.push('/'); return;
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Error al obtener proyectos.');
                }

                const respuesta = await response.json(); 
                
                const dataProyectos = respuesta.data || [];
                const rolesContext = respuesta.roles_context || {};

                // Mapear proyectos e inyectar Rol
                this.proyectos = dataProyectos.map(p => ({
                    ...p,
                    mi_rol: rolesContext[p.id] || 'OBSERVADOR', 
                    tipo_industria: p.tipo_industria || 'General',
                    activo: true, 
                }));

                this.totalRecords = respuesta.total || 0;
                this.totalPages = respuesta.total_pages || 1;

            } catch (error) {
                this.error = 'Error: ' + error.message;
                this.proyectos = [];
            } finally {
                this.loading = false;
            }
        },
        
        // -----------------------------------------------------------------------
        // ACCIONES
        // -----------------------------------------------------------------------
        
        confirmarEliminacion(proyecto) {
            if (proyecto.mi_rol !== 'PROPIETARIO') {
                alert("No tienes permisos para eliminar este proyecto.");
                return;
            }
            this.proyectoEliminarId = proyecto.id;
            this.mostrarModalEliminar = true;
        },

        handleEditClick(proyecto) {
            if (proyecto.mi_rol !== 'PROPIETARIO') {
                alert("No tienes permisos para editar este proyecto.");
                return;
            }
            this.proyectoSeleccionado = proyecto;
            this.mostrarModalEditar = true;
        },

        async eliminar(id) {
            const token = localStorage.getItem('accessToken');
            const url = `${API_BASE_URL}/api/proyectos/${id}`; 

            if (!token) {
                alert("Error: Sesión no válida.");
                return;
            }

            try {
                const response = await fetch(url, {
                    method: 'DELETE',
                    headers: { 'Authorization': `Bearer ${token}` },
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || data.message || 'Error al eliminar.');
                }

                alert('Proyecto eliminado exitosamente.');
                this.cargarProyectos(); 
                this.cerrarModalEliminar();

            } catch (err) {
                alert('Error: ' + err.message);
                this.cerrarModalEliminar();
            }
        }, 

        // -----------------------------------------------------------------------
        // EVENTOS DE MODALES
        // -----------------------------------------------------------------------
        
        handleProyectoCreado() {
            this.cargarProyectos(); 
            this.mostrarModalCrear = false;
        },
        
        handleProyectoActualizado() {
            this.closeEditModal(); 
            this.cargarProyectos(); 
        },

        cerrarModalCrear() { this.mostrarModalCrear = false; },
        closeEditModal() { this.mostrarModalEditar = false; this.proyectoSeleccionado = null; },
        closeShareModal() { this.mostrarModalCompartir = false; this.proyectoCompartirId = null; },
        cerrarModalEliminar() { this.mostrarModalEliminar = false; this.proyectoEliminarId = null; },

        openShareModal(proyectoId) {
            this.proyectoCompartirId = proyectoId;
            this.mostrarModalCompartir = true;
        }
    }
};
</script>

<style scoped lang="scss">


// ----------------------------------------
// CONTENEDOR PRINCIPAL
// ----------------------------------------
.mis-proyectos-contenido {
    max-width: 1650px;      
    margin: 0 auto;         
    padding: 30px 40px;     
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 30px;
}

// ----------------------------------------
// HEADER / TOP BAR
// ----------------------------------------
.proyectos-header-view {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    gap: 25px;
    margin-top: 10px;

    .left-group {
        display: flex;
        flex-direction: column;
        gap: 5px;

        .count-total {
            color: $GRAY;
            font-size: 1.1rem;
            letter-spacing: .3px;

            strong { 
                color: $PRIMARY-PURPLE;
                font-weight: 600;
                font-size: 1.25rem;
            }
        }
    }

    .actions-group {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-left: auto;

        .search-box {
            width: 310px;
            position: relative;

            .search-icon {
                position: absolute;
                left: 14px;
                top: 50%;
                transform: translateY(-50%);
                color: $GRAY;
                font-size: 1rem;
            }

            .search-input {
                width: 100%;
                padding: 11px 16px 11px 42px;
                border-radius: 12px;
                border: 1px solid rgba($WHITE, .08);
                background-color: $DARK-INPUT-BG;
                color: $LIGHT-TEXT;
                font-size: .95rem;
                transition: 0.2s;

                &:focus {
                    border-color: $PRIMARY-PURPLE;
                    box-shadow: 0 0 0 3px rgba($PRIMARY-PURPLE, .15);
                }
            }
        }

        .btn-nuevo-proyecto {
            background: $SUCCESS;
            color: $WHITE;
            border: none;
            padding: 11px 24px;
            border-radius: 12px;
            font-size: .95rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
            box-shadow: 0 3px 12px rgba($SUCCESS, .35);
            transition: 0.15s;

            &:hover { transform: translateY(-2px); }
            &:active { transform: translateY(0); }
        }
    }
}

// ----------------------------------------
// GRID RESPONSIVE DE TARJETAS
// ----------------------------------------
.proyectos-grid {
    display: grid;
    width: 100%;
    gap: 28px;

    // Mejor distribución moderna
    grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));

    // Las tarjetas no quedan chicas aunque haya pocos items
    align-items: stretch;
}

// ----------------------------------------
// ESTADOS (EMPTY / LOADING)
// ----------------------------------------
.alerta-vacio, .alerta-loading, .alerta-error {
    text-align: center;
    padding: 40px;
    border-radius: 14px;
    margin-top: 40px;
    font-weight: 500;
    letter-spacing: 0.3px;
}

// ----------------------------------------
// PAGINACIÓN
// ----------------------------------------
.pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 40px;
    padding-bottom: 20px;

    .btn-page {
        background: transparent;
        border: 1px solid $PRIMARY-PURPLE;
        color: $PRIMARY-PURPLE;
        padding: 8px 18px;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: .15s;

        &:hover:not(:disabled) {
            background-color: $PRIMARY-PURPLE;
            color: $WHITE;
        }

        &:disabled {
            opacity: .4;
            cursor: not-allowed;
        }
    }

    .page-info {
        font-weight: 500;
        color: $GRAY;
    }
}

// ----------------------------------------
// DARK MODE
// ----------------------------------------
.theme-dark {
    .alerta-vacio {
        background-color: rgba($WHITE, .04);
        color: $LIGHT-TEXT;
        border: 1px dashed rgba($WHITE, .15);
    }
    .alerta-error { color: $DANGER; }
    .alerta-loading { color: $LIGHT-TEXT; }
}

</style>
