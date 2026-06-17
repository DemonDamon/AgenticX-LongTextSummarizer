#!/bin/bash

export http_proxy=http://10.0.0.5:3128; export https_proxy=https://10.0.0.5:3128

# 定义进程名称和路径
root_path="/opt/liziran/email_abstraction"
cli="api_server.py --config config.json"
conda_env="/home/richsos/miniconda3/envs/liziran/bin/python"

# 查询进程ID
process_id=$(ps aux | grep -i "$cli" | grep -v grep | awk '{print $2}')

# 根据输入参数执行相应操作
case "$1" in
  start)
    if [[ -n $process_id ]]; then
      echo "邮件摘要服务已经在运行，进程ID为：$process_id"
    else
      echo "启动邮件摘要服务..."
      cd $root_path
      nohup $conda_env $cli > email_abstraction.log 2>&1 &
      echo "邮件摘要服务已启动，日志输出到$root_path/email_abstraction.log"
    fi
    ;;
  restart)
    if [[ -n $process_id ]]; then
      echo "重启邮件摘要服务..."
      kill $process_id
      cd $root_path
      nohup $conda_env $cli > email_abstraction.log 2>&1 &
      echo "邮件摘要服务已重启，日志输出到$root_path/email_abstraction.log"
    else
      echo "邮件摘要服务未运行，无法重启"
    fi
    ;;
  stop)
    if [[ -n $process_id ]]; then
      echo "关闭邮件摘要服务进程，进程ID为：$process_id"
      kill -9 $process_id
    else
      echo "邮件摘要服务未运行，无需关闭"
    fi
    ;;
  *)
    echo "Usage: $0 {start|restart|stop}"
    exit 1
    ;;
esac

exit 0