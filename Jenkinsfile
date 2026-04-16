pipeline {
    agent any

    triggers {
        cron('H/15 * * * *')
    }

    environment {
        ALERT_EMAIL   = 'wardogepochta@gmail.com'
        MAX_LATENCY   = '5.0'
        MAX_GPU_UTIL  = '90'
    }

    stages {
        stage('Health Check & Recovery') {
            steps {
                script {
                    def unhealthy = sh(script: "docker ps -q -f health=unhealthy", returnStdout: true).trim()
                    
                    if (unhealthy) {
                        echo "Detected unhealthy services. Restarting stack..."
                        sh 'docker compose restart'
                    } else {
                        echo "All services are healthy."
                    }
                }
            }
        }

        stage('E2E Checks & Latency') {
            steps {
                script {
                    def latencyOutput = sh(
                        script: "/usr/bin/time -f '%e' python3 validate.py chat --prompt 'test' --image test.jpg 2>&1 | tail -n 1",
                        returnStdout: true
                    ).trim()
                    
                    env.CURRENT_LATENCY = latencyOutput

                    if (latencyOutput.toDouble() > env.MAX_LATENCY.toDouble()) {
                        env.OVERLOAD_LATENCY = 'true'
                    }
                }
            }
        }

        stage('Resource Usage') {
            steps {
                script {
                    def gpuOutput = sh(
                        script: "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -n 1",
                        returnStdout: true
                    ).trim()
                    
                    env.CURRENT_GPU = gpuOutput ?: '0'

                    if (env.CURRENT_GPU.toInteger() > env.MAX_GPU_UTIL.toInteger()) {
                        env.OVERLOAD_GPU = 'true'
                    }
                }
            }
        }

        stage('Capacity Alerting') {
            when {
                anyOf {
                    environment name: 'OVERLOAD_LATENCY', value: 'true'
                    environment name: 'OVERLOAD_GPU', value: 'true'
                }
            }
            steps {
                emailext(
                    to: "${ALERT_EMAIL}",
                    subject: "ALERT: Capacity insufficient on Inference Gateway",
                    body: "System overloaded! GPU Util: ${env.CURRENT_GPU}%. Latency: ${env.CURRENT_LATENCY}s. Recommendation: Add another serving machine."
                )
            }
        }
    }

    post {
        failure {
            emailext(
                to: "${ALERT_EMAIL}",
                subject: "CRITICAL: Validation Pipeline Failed",
                body: "Check Jenkins console. E2E tests or health checks completely failed."
            )
        }
    }
}
