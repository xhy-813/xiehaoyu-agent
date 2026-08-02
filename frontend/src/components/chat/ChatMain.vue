<template>
  <ChatWidget>
    <template #empty>
      <WelcomeCard />
    </template>
  </ChatWidget>
</template>

<script setup lang="ts">
import ChatWidget from './ChatWidget.vue'
import WelcomeCard from './WelcomeCard.vue'
</script>