<template>
    <div class="lista-proyectos">
        <div v-if="error" class="alerta-error">{{ error }}</div>
        <div v-else-if="proyectos.length === 0" class="alerta-vacio">
             <i class="fas fa-box-open"></i> Aún no cuentas con Proyectos. 
        </div>

        <div class="proyectos-header-view">
            <div class="proyectos-status-info">
                <span class="count-total">{{ proyectos.length }} ecosistemas</span>
                <span class="count-active" v-if="proyectosActivos > 0">+{{ proyectosActivos }} activos</span>
            </div>
            
            <button class="btn-nuevo-proyecto" @click="mostrarModalCrear = true">
                <i class="fas fa-plus icon-space"></i> Nuevo Proyecto
            </button>
        </div>

        <div class="proyectos-grid">
            <TarjetaProyecto 
                v-for="proyecto in proyectos" 
                :key="proyecto.id" 
                :proyecto="proyecto" 
                @toggle-activo="toggleActivo"
                @recargar="cargarProyectos" 
            />
        </div>

        <ModalEliminarProyecto
            :class="{ modal: true, advertencia: true, visible: mostrarModalEliminar }"
            @cancelar="cerrarModalEliminar"
            @confirmar="eliminar(proyectoEliminarId, id_usuario)"
        />

        <ModalProyecto 
            v-if="mostrarModalCrear"
            @crear="crearProyecto"
            @cerrar="cerrarModalCrear"
        />
    </div>
</template>

<script>
// Importa los modales que tenías en MisProyectos.vue
import TarjetaProyecto from './TarjetaProyecto.vue'; // Componente de tarjeta reutilizable
import ModalProyecto from './CrearProyecto.vue';
import ModalEliminarProyecto from './ModalEliminar.vue';

// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
    name: 'ListaProyectos',
    components: {
        TarjetaProyecto,
        ModalProyecto,
        ModalEliminarProyecto
    },
    data() {
        return {
            proyectos: [],
            mostrarModalEliminar: false,
            proyectoEliminarId: null,
            mostrarModalCrear: false,
            id_usuario: null,
            tipo_usuario: null,
            error: null,
        };
    },
    computed: {
        proyectosActivos() {
             return this.proyectos.filter(p => p.activo).length; 
        }
    },
    mounted() {
        this.cargarProyectos();
    },
    methods: {
        async cargarProyectos() {
            const resultado = JSON.parse(localStorage.getItem('resultado'));
            const token = localStorage.getItem('accessToken'); 

            if (!resultado || !token) {
                this.error = 'Sesión no válida. Redirigiendo a Inicio...';
                this.$router.push('/');
                return;
            }

            this.id_usuario = resultado.usuario.id;
            this.tipo_usuario = resultado.usuario.tipo_usuario;
            
            let url = `${API_BASE_URL}/proyectos`; // Admin ve todos
            if (this.tipo_usuario !== 'admin') {
                url = `${API_BASE_URL}/proyectos/usuario/${this.id_usuario}`; // Usuario común
            }
            
            try {
                const response = await fetch(url, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${token}`, 
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Error al obtener proyectos.');
                }

                const data = await response.json();
                
                // 🚨 Asignación de datos con valores de ejemplo para la estética:
                this.proyectos = data.map(p => ({
                    ...p,
                    estado_texto: p.activo ? 'Activo' : 'Mantenimiento',
                    // Valores de prueba. Reemplaza con datos reales de tu API
                    icono: p.tipo_industria === 'Agricola' ? 'fas fa-leaf' : 'fas fa-building',
                    icono_gradient: p.activo ? 'linear-gradient(to right, #00C853, #1ABC9C)' : 'linear-gradient(to right, #FF8C00, #FFA500)',
                    dispositivos_count: 8,
                    sensores_count: 15,
                    ultima_actualizacion: 'Hace 2 minutos',
                })); 
            } catch (error) {
                this.error = 'Error de conexión o API: ' + error.message;
                console.error(error);
            }
        },
        // Mantiene la funcionalidad de crear/eliminar/modal, pero simplificada
        crearProyecto(proyecto) {
            this.proyectos.push(proyecto); 
            this.mostrarModalCrear = false;
        },
        cerrarModalCrear() {
            this.mostrarModalCrear = false;
        },
        confirmarEliminacion(id) {
            this.proyectoEliminarId = id;
            this.mostrarModalEliminar = true;
        },
        cerrarModalEliminar() {
            this.mostrarModalEliminar = false;
            this.proyectoEliminarId = null;
        },
        toggleActivo(id) {
            // Lógica para cambiar el estado activo del proyecto en la API
            console.log(`Toggle activo para proyecto ${id}`);
        },
        // La función eliminar debe ser ASYNC y usar el token JWT
        async eliminar(id, usuarioId) {
            const token = localStorage.getItem('accessToken');

            try {
                const response = await fetch(`${API_BASE_URL}/eliminar_proyecto?id=${id}&usuarioId=${usuarioId}`, {
                    method: 'DELETE',
                    headers: {
                       'Authorization': `Bearer ${token}`, 
                    },
                });

                if (!response.ok) {
                    throw new Error('Error al eliminar el proyecto.');
                }
                alert('Proyecto eliminado exitosamente.');
                this.proyectos = this.proyectos.filter(p => p.id !== id);
                this.cerrarModalEliminar();

            } catch (err) {
                alert('Error: ' + err.message);
                this.cerrarModalEliminar();
            }
        },
    }
};
</script>

<style scoped lang="scss">
// ----------------------------------------
// VARIABLES SCSS (Mismas de IoT Spectrum)
// ----------------------------------------
$PRIMARY-PURPLE: #8A2BE2; 
$SUCCESS-COLOR: #1ABC9C; 
$LIGHT-TEXT: #E4E6EB;
$DARK-TEXT: #333333;

.lista-proyectos {
    padding-top: 20px;
}

.proyectos-header-view {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    padding-left: 5px; 

    .proyectos-status-info {
        font-size: 1.1rem;
        font-weight: 500;
        
        // .count-total { } // Eliminado porque no tiene reglas
        .count-active {
            color: $SUCCESS-COLOR; 
            font-weight: 700;
            margin-left: 10px;
        }
    }
    
    .btn-nuevo-proyecto {
        background: $SUCCESS-COLOR;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 10px rgba($SUCCESS-COLOR, 0.3);
        transition: opacity 0.2s;

        &:hover {
            opacity: 0.9;
        }
        .icon-space {
            margin-right: 8px;
        }
    }
}

// 🚨 Rejilla principal para las tarjetas (similar al dashboard)
.proyectos-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* 3 o 4 columnas fluidas */
    gap: 25px;
}

// Estilos de tema para la info de status
.theme-dark .proyectos-status-info .count-total {
    color: rgba(255, 255, 255, 0.8);
}
.theme-light .proyectos-status-info .count-total {
    color: $DARK-TEXT;
}

.alerta-error, .alerta-vacio {
    margin-top: 20px;
    padding: 15px;
    border-radius: 8px;
    background-color: #f8d7da;
    color: #721c24;
    font-weight: 600;
}
.theme-dark .alerta-error {
    background-color: #4f1b20;
    color: #ffcccc;
}
</style>