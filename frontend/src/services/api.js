import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000, // 5分钟超时，因为生成音频可能需要较长时间
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API 错误:', error)
    // 尝试从不同位置获取错误信息
    const message = error.response?.data?.detail 
      || error.response?.data?.message 
      || error.message 
      || '请求失败'
    const errorObj = new Error(message)
    // 保留原始错误信息以便调试
    errorObj.response = error.response
    errorObj.originalError = error
    return Promise.reject(errorObj)
  }
)

// API 方法
export const apiService = {
  // 获取模型信息
  getModelInfo() {
    return api.get('/model/info')
  },

  // 上传音色参考音频
  uploadVoice(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/upload/voice', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 保存音色
  saveVoice(voiceName, file) {
    const formData = new FormData()
    formData.append('voice_name', voiceName)
    formData.append('file', file)
    return api.post('/voice/save', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 获取音色列表
  getVoiceList() {
    return api.get('/voice/list')
  },

  // 获取音色文件URL
  getVoiceUrl(filename) {
    return `/voices/${filename}`
  },

  // 预览文本分句
  previewSegments(text, maxTextTokensPerSegment = 120) {
    return api.post('/segments/preview', {
      text,
      max_text_tokens_per_segment: maxTextTokensPerSegment,
    })
  },

  // 生成音频
  generateAudio(params) {
    const formData = new FormData()
    
    // 添加基本参数
    formData.append('text', params.text)
    formData.append('spk_audio_path', params.spkAudioPath)
    formData.append('emo_control_method', params.emoControlMethod)
    formData.append('emo_weight', params.emoWeight || 0.65)
    formData.append('max_text_tokens_per_segment', params.maxTextTokensPerSegment || 120)
    
    // 添加情感控制相关参数
    if (params.emoRefPath) {
      formData.append('emo_ref_path', params.emoRefPath)
    }
    if (params.emoText) {
      formData.append('emo_text', params.emoText)
    }
    formData.append('emo_random', params.emoRandom || false)
    
    // 添加情感向量（8个维度）
    if (params.emoVector && Array.isArray(params.emoVector)) {
      params.emoVector.forEach((val, index) => {
        formData.append(`vec${index + 1}`, val || 0.0)
      })
    } else {
      // 如果没有提供向量，默认全部为0
      for (let i = 1; i <= 8; i++) {
        formData.append(`vec${i}`, 0.0)
      }
    }
    
    // 添加高级参数
    formData.append('do_sample', params.doSample !== false)
    formData.append('top_p', params.topP || 0.8)
    formData.append('top_k', params.topK || 30)
    formData.append('temperature', params.temperature || 0.8)
    formData.append('length_penalty', params.lengthPenalty || 0.0)
    formData.append('num_beams', params.numBeams || 3)
    formData.append('repetition_penalty', params.repetitionPenalty || 10.0)
    formData.append('max_mel_tokens', params.maxMelTokens || 1500)
    
    return api.post('/generate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // 获取示例列表
  getExamples() {
    return api.get('/examples/list')
  },

  // 获取输出音频URL
  getOutputAudioUrl(filename) {
    return `/outputs/${filename}`
  },

  // 获取示例音频URL
  getExampleAudioUrl(filename) {
    return `/examples/${filename}`
  },
}

export default apiService

