<template>
    <div class="modal-base" @click.self="$emit('close')">
        <div class="modal-contenido" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
            <div class="modal-header">
                <h2>Modificar Proyecto: {{ proyecto.nombre }}</h2>
                <button @click="$emit('close')" class="btn-cerrar">&times;</button>
            </div>

            <div class="modal-body">
                <ProyectoForm 
                    :initial-data="proyecto"
                    :submit-button-text="'Guardar Cambios'"
                    :loading="loading"
                    :error="error"
                    @submit="handleSubmission"
                    @cancel="$emit('close')"
                />
            </div>
        </div>
    </div>
</template>

<script>
import ProyectoForm from './ProyectoForm.vue';

// 🚨 URL LOCAL ASEGURADA
// const API_BASE_URL = 'http://127.0.0.1:8001'; 

export default {
    name: 'ModalEditarProyecto',
    components: { ProyectoForm },
    props: {
        // Objeto del proyecto completo que se va a editar
        proyecto: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            isDark: false,
            loading: false,
            error: null,
        };
    },
    mounted() {
        // Detección de tema
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.isDark = true;
        }
    },
    methods: {
        async handleSubmission(formData) {
            this.loading = true;
            this.error = null;
            const token = localStorage.getItem('accessToken');

            try {
                // Obtenemos el ID del propietario (que se pasó en la prop 'proyecto')
                const usuarioId = this.proyecto.usuario_id;
                
                const response = await fetch(`${API_BASE_URL}/api/proyectos/${this.proyecto.id}`, {
                    method: 'PUT', // Usamos PUT para actualización
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        nombre: formData.nombre,
                        descripcion: formData.descripcion,
                        // 🚨 CRÍTICO: Envío del nuevo campo
                        tipo_industria: formData.tipo_industria, 
                        usuario_id: usuarioId // ID del propietario (para autorización en el backend)
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.message || data.detail || 'Fallo al actualizar el proyecto.');
                }
                
                // Éxito: Emitir evento para que MisProyectos.vue recargue la lista
                this.$emit('updated', data.resultados[0]);
                this.$emit('close');

            } catch (err) {
                this.error = err.message || 'Error de conexión.';
            } finally {
                this.loading = false;
            }
        }
    }
};
</script>

<style scoped lang="scss">
// ----------------------------------------
// VARIABLES DE LA PALETA
// ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2;
// $SUCCESS-COLOR: #1ABC9C;
// $BLUE-MIDNIGHT: #1A1A2E;
// $DARK-TEXT: #333333;
// $LIGHT-TEXT: #E4E6EB;
// $SUBTLE-BG-DARK: #2B2B40; 
// $SUBTLE-BG-LIGHT: #FFFFFF;

// ----------------------------------------
// BASE DEL MODAL (POSICIONAMIENTO CRÍTICO)
// ----------------------------------------
.modal-base {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background-color: rgba(0, 0, 0, 0.6);
    display: flex; justify-content: center; align-items: center;
    z-index: 9999;
}

.modal-contenido {
    width: 90%; max-width: 600px; /* Ancho para edición */
    border-radius: 15px; padding: 25px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
    transition: background-color 0.3s;
}

.modal-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 20px;
    h2 { font-size: 1.4rem; font-weight: 600; }
}

.btn-cerrar {
    background: none; border: none; font-size: 1.8rem; cursor: pointer; opacity: 0.7;
    &:hover { opacity: 1; }
}

// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------
.theme-light { background-color: $SUBTLE-BG-LIGHT; color: $DARK-TEXT; }
.theme-dark { 
    background-color: $SUBTLE-BG-DARK; 
    color: $LIGHT-TEXT; 
    
    .form-control { /* Estilos para el input dentro del modal */
        background-color: $BLUE-MIDNIGHT; 
        border: 1px solid rgba($LIGHT-TEXT, 0.2); 
        color: $LIGHT-TEXT; 
    }
    .btn-secondary { /* Botón Cancelar */
        background-color: #444; 
        color: $LIGHT-TEXT; 
        border: none; 
    }
}
</style>