<template>
  <div v-if="uploadState.mostrarWidget" class="widget-flotante">
    <div class="widget-header">
      <i class="bi bi-cloud-arrow-up-fill text-primary"></i>
      <span>Sincronizando IoT</span>
      <button @click="cerrarWidget" class="btn-cerrar"><i class="bi bi-x"></i></button>
    </div>
    
    <div class="widget-body">
      <div v-if="uploadState.uploading" class="progreso-text">
        {{ uploadState.progress }}% completado
      </div>
      <div v-else class="progreso-text" :class="uploadState.status.type">
        {{ uploadState.status.message }}
      </div>
      
      <div class="barra-base">
        <div class="barra-relleno" :style="{ width: uploadState.progress + '%' }"></div>
      </div>
      
      <small v-if="uploadState.uploading">{{ uploadState.processedRows }} / {{ uploadState.totalRows }} filas</small>
    </div>
  </div>
</template>

<script setup>
import { uploadState } from '@/stores/uploadStore.js';

const cerrarWidget = () => {
  uploadState.mostrarWidget = false;
};
</script>

<style scoped>
.widget-flotante {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 300px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
  z-index: 9999;
  border: 1px solid #eee;
  overflow: hidden;
}
.widget-header {
  background: #f8f9fa;
  padding: 10px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  border-bottom: 1px solid #eee;
}
.btn-cerrar {
  background: none; border: none; cursor: pointer; font-size: 1.2rem;
}
.widget-body {
  padding: 15px;
}
.barra-base {
  width: 100%; height: 8px; background: #eee; border-radius: 4px; margin: 10px 0; overflow: hidden;
}
.barra-relleno {
  height: 100%; background: #8A2BE2; transition: width 0.3s ease;
}
.progreso-text { font-size: 0.9rem; font-weight: bold; }
.success { color: #1ABC9C; }
.error { color: #E74C3C; }
</style>