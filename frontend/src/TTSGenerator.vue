<template>
    <div class="tts-generator">
      <div class="header-card">
        <div class="header-content">
          <h2>IndexTTS2: 工业级可控且高效的零样本文本转语音系统</h2>
        </div>
      </div>
  
      <el-tabs v-model="activeTab" class="main-tabs">
        <el-tab-pane label="音频生成" name="generate">
          <!-- 中间部分：左侧已保存音色，中间流程，右侧高级参数 -->
          <el-row :gutter="20">
            <!-- 左侧：已保存音色列表 -->
            <el-col :span="6">
              <el-card>
                <template #header>
                  <span>已保存音色</span>
                </template>
                
                <el-select
                  v-model="selectedSavedVoice"
                  placeholder="选择已保存音色"
                  filterable
                  class="select-full-width"
                  @change="handleLoadSavedVoice"
                >
                  <el-option
                    v-for="voice in savedVoices"
                    :key="voice"
                    :label="voice"
                    :value="voice"
                  />
                </el-select>
  
                <el-button
                  type="info"
                  :icon="Refresh"
                  @click="loadVoiceList"
                  class="btn-refresh"
                >
                  刷新列表
                </el-button>
              </el-card>

              <!-- 情感控制设置 -->
              <el-card style="margin-top: 20px">
                <template #header>
                  <span>情感控制设置</span>
                </template>

                <el-radio-group v-model="emoControlMethod" @change="handleEmoMethodChange">
                  <el-radio :label="0">与音色参考音频相同</el-radio>
                  <el-radio :label="1">使用情感参考音频</el-radio>
                  <el-radio :label="2">使用情感向量控制</el-radio>
                </el-radio-group>

                <!-- 情感参考音频 -->
                <div v-if="emoControlMethod === 1" class="emo-section">
                  <div v-if="emoAudioUrl" class="emo-audio-container">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                      <span>情感参考音频</span>
                      <el-button
                        text
                        type="danger"
                        size="small"
                        @click="handleClearEmoAudio"
                      >
                        <el-icon><Close /></el-icon>
                      </el-button>
                    </div>
                    <audio :src="emoAudioUrl" controls class="audio-full-width"></audio>
                  </div>
                  <div v-else>
                    <el-upload
                      :auto-upload="false"
                      :on-change="handleEmoUpload"
                      :show-file-list="false"
                      accept="audio/*"
                      drag
                      class="voice-upload-drag"
                    >
                      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                      <div class="el-upload__text">
                        将音频文件拖到此处，或<em>点击上传</em>
                      </div>
                      <template #tip>
                        <div class="el-upload__tip">
                          支持 wav、mp3、flac 等音频格式
                        </div>
                      </template>
                    </el-upload>
                  </div>
                </div>

                <!-- 情感向量控制 -->
                <div v-if="emoControlMethod === 2" class="emo-section">
                  <div v-for="(label, index) in emotionLabels" :key="index" class="emo-vector-item">
                    <el-slider
                      v-model="emoVector[index]"
                      :min="0"
                      :max="1"
                      :step="0.05"
                      :label="label"
                      show-input
                    />
                  </div>
                  <el-checkbox v-model="emoRandom" class="emo-random-checkbox">
                    情感随机采样
                  </el-checkbox>
                </div>

                <!-- 情感权重 -->
                <div v-if="emoControlMethod !== 0" class="emo-section">
                  <el-slider
                    v-model="emoWeight"
                    :min="0"
                    :max="1"
                    :step="0.01"
                    label="情感权重"
                    show-input
                  />
                  <div class="emo-weight-hint">
                    建议0.6-0.8之间
                  </div>
                </div>
              </el-card>
            </el-col>

            <!-- 中间：文本输入和生成 -->
            <el-col :span="12">
              <el-card>
                <template #header>
                  <span>生成流程</span>
                </template>
                
                <!-- 音色参考音频 -->
                <div class="voice-reference-section">
                  <div class="section-label">
                    <span>音色参考音频</span>
                    <el-button
                      v-if="currentVoiceUrl"
                      text
                      type="danger"
                      size="small"
                      @click="handleClearVoice"
                      style="margin-left: 10px;"
                    >
                      <el-icon><Close /></el-icon>
                    </el-button>
                  </div>
                  <div v-if="currentVoiceUrl" class="audio-player">
                    <audio :src="currentVoiceUrl" controls class="audio-full-width"></audio>
                  </div>
                  <div v-else>
                    <el-upload
                      :auto-upload="false"
                      :on-change="handleVoiceUpload"
                      :show-file-list="false"
                      accept="audio/*"
                      drag
                      class="voice-upload-drag"
                    >
                      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                      <div class="el-upload__text">
                        将音频文件拖到此处，或<em>点击上传</em>
                      </div>
                      <template #tip>
                        <div class="el-upload__tip">
                          支持 wav、mp3、flac 等音频格式
                        </div>
                      </template>
                    </el-upload>
                  </div>
                </div>

                <!-- 向下箭头 -->
                <div class="flow-arrow">
                  <el-icon :size="30" color="var(--ctp-text)">
                    <ArrowDown />
                  </el-icon>
                </div>
                
                <!-- 文本输入 -->
                <div class="text-input-section">
                  <div class="section-label">文本输入</div>
                  <el-input
                    v-model="inputText"
                    type="textarea"
                    :rows="8"
                    placeholder="请输入目标文本"
                    @input="handleTextChange"
                  />
                </div>

                <!-- 生成按钮 -->
                <el-button
                  type="primary"
                  :icon="VideoPlay"
                  :loading="isGenerating"
                  :disabled="!canGenerate"
                  @click="handleGenerate"
                  class="btn-generate"
                >
                  {{ isGenerating ? '生成中...' : '生成语音' }}
                </el-button>

                <!-- 生成进度条 -->
                <el-progress
                  :percentage="generateProgress"
                  :status="generateProgress === 100 ? 'success' : (isGenerating ? undefined : '')"
                  :stroke-width="8"
                  :show-text="isGenerating || generateProgress > 0"
                  style="margin: 15px 0;"
                >
                  <template #default="{ percentage }">
                    <span style="color: var(--ctp-text);">
                      {{ percentage === 100 ? '生成完成！' : (isGenerating ? '正在生成音频...' : '') }}
                    </span>
                  </template>
                </el-progress>

                <!-- 固定的输出音频框 -->
                <div class="output-audio-section">
                  <div class="section-label">
                    <span>输出音频</span>
                    <el-button
                      v-if="outputAudioUrl"
                      text
                      type="primary"
                      size="small"
                      :icon="Download"
                      @click="handleDownloadAudio"
                      style="margin-left: 10px;"
                    >
                      下载
                    </el-button>
                  </div>
                  <div v-if="outputAudioUrl" class="audio-player">
                    <audio :src="outputAudioUrl" controls class="audio-full-width"></audio>
                  </div>
                  <div v-else class="no-output-hint">
                    <el-icon :size="48" color="var(--ctp-subtext0)">
                      <VideoPlay />
                    </el-icon>
                    <div style="margin-top: 10px; color: var(--ctp-subtext0); font-size: 13px;">
                      生成音频后将显示在这里
                    </div>
                  </div>
                </div>
              </el-card>
            </el-col>
  
            <!-- 右侧：高级设置 -->
            <el-col :span="6">
              <el-card class="advanced-settings-card">
                <template #header>
                  <el-collapse>
                    <el-collapse-item title="高级生成参数设置" name="advanced">
                      <div>
                        <div class="param-item-with-label">
                          <span class="param-label">do_sample：</span>
                          <el-checkbox v-model="doSample">是否进行采样</el-checkbox>
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">temperature：</span>
                          <span class="param-desc">控制生成的随机性，值越大越随机</span>
                          <el-slider
                            v-model="temperature"
                            :min="0.1"
                            :max="2.0"
                            :step="0.1"
                            show-input
                            class="advanced-param-item"
                          />
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">top_p：</span>
                          <span class="param-desc">核采样，保留累计概率达到该值的token</span>
                          <el-slider
                            v-model="topP"
                            :min="0"
                            :max="1"
                            :step="0.01"
                            show-input
                            class="advanced-param-item"
                          />
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">top_k：</span>
                          <span class="param-desc">仅考虑概率最高的k个token</span>
                          <el-slider
                            v-model="topK"
                            :min="0"
                            :max="100"
                            :step="1"
                            show-input
                            class="advanced-param-item"
                          />
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">num_beams：</span>
                          <span class="param-desc">束搜索的束数量，值越大质量越好但速度越慢</span>
                          <el-slider
                            v-model="numBeams"
                            :min="1"
                            :max="10"
                            :step="1"
                            show-input
                            class="advanced-param-item"
                          />
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">repetition_penalty：</span>
                          <span class="param-desc">重复惩罚系数，防止重复生成</span>
                          <el-input-number
                            v-model="repetitionPenalty"
                            :min="0.1"
                            :max="20.0"
                            :step="0.1"
                            class="advanced-number-input"
                          />
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">length_penalty：</span>
                          <span class="param-desc">长度惩罚，控制生成长度偏好</span>
                          <el-input-number
                            v-model="lengthPenalty"
                            :min="-2.0"
                            :max="2.0"
                            :step="0.1"
                            class="advanced-number-input"
                          />
                        </div>
                        <div class="param-item-with-label">
                          <span class="param-label">max_mel_tokens：</span>
                          <span class="param-desc">生成Token最大数量，过小导致音频被截断</span>
                          <el-slider
                            v-model="maxMelTokens"
                            :min="50"
                            :max="maxMelTokensLimit"
                            :step="10"
                            show-input
                            class="advanced-param-item"
                          />
                        </div>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </template>
  
                <div>
                  <div class="segment-config">
                    <label>分句最大Token数</label>
                    <el-slider
                      v-model="maxTextTokensPerSegment"
                      :min="20"
                      :max="maxTextTokensLimit"
                      :step="2"
                      show-input
                    />
                    <div class="segment-hint">
                      建议80~200之间
                    </div>
                  </div>
  
                  <el-button
                    text
                    type="primary"
                    @click="showSegmentPreview = !showSegmentPreview"
                  >
                    {{ showSegmentPreview ? '隐藏' : '显示' }}分句预览
                  </el-button>
  
                  <el-table
                    v-if="showSegmentPreview && segments.length > 0"
                    :data="segments"
                    size="small"
                    class="segment-table"
                    max-height="200"
                  >
                    <el-table-column prop="index" label="序号" width="60" />
                    <el-table-column prop="text" label="分句内容" show-overflow-tooltip />
                    <el-table-column prop="tokens" label="Token数" width="80" />
                  </el-table>
                </div>
              </el-card>
            </el-col>
          </el-row>
  
          <!-- 示例 -->
          <el-card class="examples-card">
            <template #header>
              <span>示例</span>
              <el-button
                text
                type="primary"
                @click="loadExamples"
                class="btn-float-right"
              >
                刷新示例
              </el-button>
            </template>

            <div class="examples-list">
              <div
                v-for="(example, index) in examples"
                :key="index"
                class="example-card"
              >
                <div class="example-content">
                  <div class="example-text">
                    <div class="example-label">文本：</div>
                    <div class="example-text-content">{{ example.text }}</div>
                  </div>
                  
                  <div class="example-audios">
                    <div v-if="example.prompt_audio" class="example-audio-item">
                      <div class="example-label">音色参考：</div>
                      <audio
                        :src="example.prompt_audio"
                        controls
                        class="example-audio"
                      />
                    </div>
                    
                    <div v-if="example.emo_audio" class="example-audio-item">
                      <div class="example-label">情感参考：</div>
                      <audio
                        :src="example.emo_audio"
                        controls
                        class="example-audio"
                      />
                    </div>
                  </div>
                </div>
                
                <div class="example-actions">
                  <el-button
                    type="primary"
                    size="small"
                    @click="loadExample(example)"
                  >
                    加载
                  </el-button>
                </div>
              </div>
              
              <div v-if="examples.length === 0" class="examples-empty">
                暂无示例
              </div>
            </div>
          </el-card>
        </el-tab-pane>
      </el-tabs>
    </div>
  </template>
  
  <script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import {
    UploadFilled,
    VideoPlay,
    Upload,
    Refresh,
    ArrowDown,
    Close,
    Download,
  } from '@element-plus/icons-vue'
  import apiService from '@/services/api'
  import '@/components/TTSGenerator.css'
  
  // 数据定义
  const activeTab = ref('generate')
  const modelVersion = ref('2.0')
  const inputText = ref('')
  const currentVoiceFile = ref(null)
  const currentVoiceUrl = ref('')
  const voiceName = ref('')
  const savedVoices = ref([])
  const selectedSavedVoice = ref('')
  const isGenerating = ref(false)
  const generateProgress = ref(0)
  const outputAudioUrl = ref('')
  
  // 情感控制
  const emoControlMethod = ref(0)
  const emoAudioFile = ref(null)
  const emoAudioUrl = ref('')
  const emoWeight = ref(0.65)
  const emoRandom = ref(false)
  const emoVector = ref([0, 0, 0, 0, 0, 0, 0, 0])
  const emotionLabels = ['喜', '怒', '哀', '惧', '厌恶', '低落', '惊喜', '平静']
  
  // 高级参数
  const doSample = ref(true)
  const temperature = ref(0.8)
  const topP = ref(0.8)
  const topK = ref(30)
  const numBeams = ref(3)
  const repetitionPenalty = ref(10.0)
  const lengthPenalty = ref(0.0)
  const maxMelTokens = ref(1500)
  const maxTextTokensPerSegment = ref(120)
  
  // 分句预览
  const showSegmentPreview = ref(false)
  const segments = ref([])
  const maxTextTokensLimit = ref(300)
  const maxMelTokensLimit = ref(2000)
  
  // 示例
  const examples = ref([])
  
  // 计算属性
  const canGenerate = computed(() => {
    return inputText.value.trim() && currentVoiceFile.value && !isGenerating.value
  })
  
  // 方法
  const loadModelInfo = async () => {
    try {
      const info = await apiService.getModelInfo()
      modelVersion.value = info.model_version || '2.0'
      if (info.max_text_tokens) {
        maxTextTokensLimit.value = info.max_text_tokens
      }
      if (info.max_mel_tokens) {
        maxMelTokensLimit.value = info.max_mel_tokens
      }
    } catch (error) {
      ElMessage.error(`加载模型信息失败: ${error.message}`)
    }
  }

  // 处理音色上传
  const handleVoiceUpload = (file) => {
    currentVoiceFile.value = file.raw
    currentVoiceUrl.value = URL.createObjectURL(file.raw)
    selectedSavedVoice.value = '' // 清除已选择的保存音色
  }

  // 清除音色参考音频
  const handleClearVoice = () => {
    if (currentVoiceUrl.value && currentVoiceUrl.value.startsWith('blob:')) {
      URL.revokeObjectURL(currentVoiceUrl.value)
    }
    currentVoiceFile.value = null
    currentVoiceUrl.value = ''
    selectedSavedVoice.value = ''
  }

  // 清除情感参考音频
  const handleClearEmoAudio = () => {
    if (emoAudioUrl.value && emoAudioUrl.value.startsWith('blob:')) {
      URL.revokeObjectURL(emoAudioUrl.value)
    }
    emoAudioFile.value = null
    emoAudioUrl.value = ''
  }

  // 保存音色
  const handleSaveVoice = async () => {
    if (!currentVoiceFile.value) {
      ElMessage.warning('请先上传音频文件！')
      return
    }
    if (!voiceName.value || !voiceName.value.trim()) {
      ElMessage.warning('请输入音色名称！')
      return
    }

    try {
      const result = await apiService.saveVoice(voiceName.value.trim(), currentVoiceFile.value)
      ElMessage.success(result.message || '音色保存成功！')
      voiceName.value = ''
      await loadVoiceList()
      selectedSavedVoice.value = result.filename
    } catch (error) {
      ElMessage.error(`保存失败: ${error.message}`)
    }
  }

  // 加载已保存音色列表
  const loadVoiceList = async () => {
    try {
      const result = await apiService.getVoiceList()
      savedVoices.value = result.voices || []
    } catch (error) {
      ElMessage.error(`加载音色列表失败: ${error.message}`)
    }
  }

  // 加载已保存的音色
  const handleLoadSavedVoice = async (filename) => {
    if (!filename) return

    try {
      const url = apiService.getVoiceUrl(filename)
      currentVoiceUrl.value = url
      
      // 通过 fetch 获取文件对象
      const response = await fetch(url)
      const blob = await response.blob()
      const file = new File([blob], filename, { type: blob.type })
      currentVoiceFile.value = file
      
      ElMessage.success(`已加载音色: ${filename}`)
    } catch (error) {
      ElMessage.error(`加载音色失败: ${error.message}`)
    }
  }

  // 处理文本变化（分句预览）
  const handleTextChange = async () => {
    if (!inputText.value || inputText.value.trim().length === 0) {
      segments.value = []
      return
    }

    try {
      const result = await apiService.previewSegments(
        inputText.value,
        maxTextTokensPerSegment.value
      )
      segments.value = result.segments || []
    } catch (error) {
      console.error('预览分句失败:', error)
    }
  }

  // 监听分句参数变化
  watch(maxTextTokensPerSegment, () => {
    if (inputText.value && inputText.value.trim().length > 0) {
      handleTextChange()
    }
  })

  // 处理情感控制方式变化
  const handleEmoMethodChange = () => {
    // 切换情感控制方式时，清空之前的选择
    if (emoControlMethod.value !== 1) {
      emoAudioFile.value = null
      emoAudioUrl.value = ''
    }
    if (emoControlMethod.value !== 2) {
      emoVector.value = [0, 0, 0, 0, 0, 0, 0, 0]
    }
  }

  // 处理情感音频上传
  const handleEmoUpload = (file) => {
    emoAudioFile.value = file.raw
    emoAudioUrl.value = URL.createObjectURL(file.raw)
  }

  // 生成语音
  const handleGenerate = async () => {
    if (!inputText.value || !inputText.value.trim()) {
      ElMessage.warning('请输入目标文本！')
      return
    }
    if (!currentVoiceFile.value) {
      ElMessage.warning('请先上传音色参考音频！')
      return
    }

    // 确定音色文件路径
    let spkAudioPath = ''
    if (currentVoiceFile.value instanceof File) {
      // 如果是新上传的文件，先上传到服务器
      try {
        const uploadResult = await apiService.uploadVoice(currentVoiceFile.value)
        spkAudioPath = uploadResult.file_path
      } catch (error) {
        ElMessage.error(`上传音色文件失败: ${error.message}`)
        return
      }
    } else if (selectedSavedVoice.value) {
      // 如果是已保存的音色
      spkAudioPath = `voices/${selectedSavedVoice.value}`
    } else {
      ElMessage.error('无法确定音色文件路径')
      return
    }

    // 确定情感参考音频路径
    let emoRefPath = null
    if (emoControlMethod.value === 1 && emoAudioFile.value) {
      try {
        const uploadResult = await apiService.uploadVoice(emoAudioFile.value)
        emoRefPath = uploadResult.file_path
      } catch (error) {
        ElMessage.error(`上传情感参考音频失败: ${error.message}`)
        return
      }
    }

    isGenerating.value = true
    generateProgress.value = 10
    outputAudioUrl.value = ''

    try {
      console.log('开始生成音频，参数:', {
        text: inputText.value.trim().substring(0, 50) + '...',
        spkAudioPath,
        emoControlMethod: emoControlMethod.value,
      })

      const params = {
        text: inputText.value.trim(),
        spkAudioPath: spkAudioPath,
        emoControlMethod: emoControlMethod.value,
        emoRefPath: emoRefPath,
        emoWeight: emoWeight.value,
        emoRandom: emoRandom.value,
        maxTextTokensPerSegment: maxTextTokensPerSegment.value,
        doSample: doSample.value,
        topP: topP.value,
        topK: topK.value,
        temperature: temperature.value,
        lengthPenalty: lengthPenalty.value,
        numBeams: numBeams.value,
        repetitionPenalty: repetitionPenalty.value,
        maxMelTokens: maxMelTokens.value,
      }

      // 如果是情感向量控制模式，添加向量
      if (emoControlMethod.value === 2) {
        params.emoVector = emoVector.value
      }

      generateProgress.value = 30
      
      // 模拟进度更新（因为无法获取真实进度）
      const progressInterval = setInterval(() => {
        if (generateProgress.value < 90) {
          generateProgress.value += 5
        }
      }, 1000)

      const result = await apiService.generateAudio(params)
      
      clearInterval(progressInterval)
      generateProgress.value = 100

      console.log('生成成功，结果:', result)
      
      if (result && result.filename) {
        const audioUrl = apiService.getOutputAudioUrl(result.filename)
        outputAudioUrl.value = audioUrl
        
        // 等待音频元素加载完成后再显示成功提示
        await waitForAudioLoad(audioUrl)
        ElMessage.success('音频生成成功！')
      } else {
        throw new Error('生成结果格式错误')
      }
    } catch (error) {
      console.error('生成失败:', error)
      console.error('错误详情:', {
        message: error.message,
        response: error.response,
        originalError: error.originalError
      })
      
      // 尝试从多个位置获取错误信息
      let errorMessage = '生成失败'
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message
      } else if (error.message) {
        errorMessage = error.message
      } else if (error.originalError?.response?.data?.detail) {
        errorMessage = error.originalError.response.data.detail
      }
      
      ElMessage.error(`生成失败: ${errorMessage}`)
      generateProgress.value = 0
    } finally {
      isGenerating.value = false
      // 延迟重置进度条
      setTimeout(() => {
        if (!isGenerating.value) {
          generateProgress.value = 0
        }
      }, 2000)
    }
  }

  // 等待音频加载完成
  const waitForAudioLoad = (audioUrl) => {
    return new Promise((resolve, reject) => {
      // 等待 DOM 更新
      setTimeout(() => {
        const audioElement = document.querySelector('.output-audio-section audio')
        if (!audioElement) {
          // 如果找不到音频元素，等待一下再试
          setTimeout(() => {
            const retryElement = document.querySelector('.output-audio-section audio')
            if (retryElement) {
              if (retryElement.readyState >= 2) {
                // 音频已经加载了部分数据
                resolve()
              } else {
                retryElement.addEventListener('loadeddata', () => resolve(), { once: true })
                retryElement.addEventListener('error', () => reject(new Error('音频加载失败')), { once: true })
                // 设置超时，避免无限等待
                setTimeout(() => resolve(), 3000)
              }
            } else {
              // 如果还是找不到，直接 resolve（可能音频已经可用）
              resolve()
            }
          }, 200)
        } else {
          if (audioElement.readyState >= 2) {
            // 音频已经加载了部分数据
            resolve()
          } else {
            audioElement.addEventListener('loadeddata', () => resolve(), { once: true })
            audioElement.addEventListener('error', () => reject(new Error('音频加载失败')), { once: true })
            // 设置超时，避免无限等待
            setTimeout(() => resolve(), 3000)
          }
        }
      }, 100)
    })
  }

  // 下载输出音频
  const handleDownloadAudio = async () => {
    if (!outputAudioUrl.value) {
      ElMessage.warning('没有可下载的音频')
      return
    }

    try {
      // 从 URL 获取文件名
      const urlParts = outputAudioUrl.value.split('/')
      const filename = urlParts[urlParts.length - 1] || 'output.wav'
      
      // 获取音频文件
      const response = await fetch(outputAudioUrl.value)
      if (!response.ok) {
        throw new Error('下载失败')
      }
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      ElMessage.success('音频下载成功')
    } catch (error) {
      console.error('下载失败:', error)
      ElMessage.error(`下载失败: ${error.message}`)
    }
  }

  // 加载示例列表
  const loadExamples = async () => {
    try {
      const result = await apiService.getExamples()
      examples.value = (result.examples || []).map(example => ({
        ...example,
        prompt_audio: example.prompt_audio ? apiService.getExampleAudioUrl(example.prompt_audio.split('/').pop()) : null,
        emo_audio: example.emo_audio ? apiService.getExampleAudioUrl(example.emo_audio.split('/').pop()) : null,
      }))
    } catch (error) {
      ElMessage.error(`加载示例失败: ${error.message}`)
    }
  }

  // 加载示例数据
  const loadExample = (example) => {
    // 加载音色参考音频
    if (example.prompt_audio) {
      currentVoiceUrl.value = example.prompt_audio
      // 通过 URL 加载文件
      fetch(example.prompt_audio)
        .then(res => res.blob())
        .then(blob => {
          const filename = example.prompt_audio.split('/').pop()
          currentVoiceFile.value = new File([blob], filename, { type: blob.type })
        })
    }

    // 加载文本
    if (example.text) {
      inputText.value = example.text
    }

    // 加载情感控制方式
    if (typeof example.emo_mode === 'number') {
      emoControlMethod.value = example.emo_mode
    }

    // 加载情感参考音频
    if (example.emo_audio && emoControlMethod.value === 1) {
      emoAudioUrl.value = example.emo_audio
      fetch(example.emo_audio)
        .then(res => res.blob())
        .then(blob => {
          const filename = example.emo_audio.split('/').pop()
          emoAudioFile.value = new File([blob], filename, { type: blob.type })
        })
    }

    // 加载情感权重
    if (typeof example.emo_weight === 'number') {
      emoWeight.value = example.emo_weight
    }

    // 加载情感向量
    if (example.emo_vec && Array.isArray(example.emo_vec) && emoControlMethod.value === 2) {
      emoVector.value = [...example.emo_vec]
    }

    ElMessage.success('示例加载成功！')
  }

  // 组件挂载时初始化
  onMounted(async () => {
    await loadModelInfo()
    await loadVoiceList()
    await loadExamples()
  })
</script>