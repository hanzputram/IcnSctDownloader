import { reactive } from 'vue'

export const store = reactive({
  showAddAccountModal: false,
  showAddLinkModal: false,
  botRunning: true,
  refreshTrigger: 0,
  triggerRefresh() {
    this.refreshTrigger++
  }
})
