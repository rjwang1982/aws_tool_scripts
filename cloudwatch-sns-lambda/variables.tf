variable "enable_schedule" {
  description = "是否启用定时触发器（EventBridge 每 5 分钟）"
  type        = bool
  default     = true
}