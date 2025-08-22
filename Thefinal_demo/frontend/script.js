// alert("切勿泄露任何公司內部資料!!!")
let aiInfos = [];
let isAiThinking = false;
let controller = null
const chatMessages = document.getElementById("chatMessages");
const userInput = document.getElementById("userInput");
const sendButton = document.getElementById("sendButton");
const stopButton = document.getElementById("stopButton"); 
const quickReplies = [
    "你能幫我寫一段程式碼嗎？",
    "有什麼AI可以生成聲音在影片中加入旁白?",
    "根據相關資料寫一個段落",
    "搜索關於糖尿病危害的論文",
    "讓一個圖片轉換成動畫或者live圖",
    "需要生成一個富有時尚感的logo"
]


//load ai data 
document.addEventListener("DOMContentLoaded", () => {
    fetch('aiInfos.json')
        .then(res => res.json())
        .then(data => {
            aiInfos = data.aiInfos;
            aiInfos.forEach(tool => {
                if (tool.limitations) {
                    tool.limitations = tool.limitations.replace(/\n/g, '<br>');
                }
                if (tool.description) {
                    tool.description = tool.description.replace(/\n/g, '<br>');
                }
                // if (tool.text) {
                //     tool.text = tool.text.replace(/\\n/g, '<br><br>');
                // }
            });
            console.log("AI Tools Data:", aiInfos); // 查看載入的資料
            renderCard(aiInfos); // load ai card

            const tags = document.querySelectorAll(".tag-button");
            tags.forEach(tag => {
                tag.addEventListener("click", () => {
                    filterCards(tag.dataset.tag);
                });
                tag.addEventListener("keypress", (e) => {
                    if (e.key === "Enter") {
                        filterCards(tag.dataset.tag);
                    }
                });
            });
        })
        .catch(err => console.error('載入資料失敗', err));
});


addAIMessage("你好,歡迎來到AI推薦教學平台！請問你想了解哪個AI工具？");
    
 async function sendMessage(e) {
    console.log('sendMessage called')
    if(isAiThinking){
        alert("AI正在思考中，請稍後再發送消息。");
        return;
    }
    const message = userInput.value.trim();
    if (message === ''){
        alert("請輸入消息");
        return;
    }
        addUserMessage(message);//add user message
        userInput.value = '';
        setAiThinking(true);//

        const loadingDiv = document.createElement('div');// 添加加载提示
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'AI正在思考中...';
        chatMessages.appendChild(loadingDiv);

        try {
            controller = new AbortController(); //  ADD: Create a new controller for each request
            const response = await fetch('http://127.0.0.1:5001/api/chat',{
            method: 'POST',
            headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }),
                signal: controller.signal
            }
        );
            
        if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            } 
            let data = await response.json();
            console.log("Response data:", data); // 查看返回数据

           
            console.log("Response data:", data); // 查看返回数据
            if(data && data.message){
                addAIMessage(data.message, data.matchedTool || null);  // 只調用一次
            } else {
                throw new Error("無效的回應格式");
            }}
        catch (error) {
            console.error("Error:", error); 
            if (error.name === 'AbortError') {
                // Handle abort error
                console.log("請求已被中止");
                addAIMessage("請求已被中止");
                return;
            }
        let errorMessage = "網絡錯誤，請檢查連接後重試。";
        if (error.message.includes('Failed to fetch')) {
            errorMessage = "無法連接伺服器，請檢查網絡連接。";
        } else if (error.message.includes('HTTP錯誤')) {
            if (error.message.includes('429')) {
                errorMessage = "請求過於頻繁，請稍後再試。";
            }
        } else if (error.message.includes('無效的回應格式')) {
            errorMessage = "伺服器回應格式不正確。";
        }
        addAIMessage(errorMessage);
        }
        finally{
            loadingDiv.remove();
            setAiThinking(false);
            console.log('Message sent and response received');
        };
    }

    
    sendButton.addEventListener('click', async (e) => {
        
        await sendMessage(e);
        
    });

    if (stopButton) {
        stopButton.addEventListener('click', stopAiThinking);
    }

    document.addEventListener("keydown", async (e) => {
        if (e.key === "Enter" && !e.shiftKey) { // Shift + Enter 用於換行   
            await sendMessage(e);
           
        }});

   function setAiThinking(state) {
    isAiThinking = state;
    
    // Send button
    sendButton.disabled = state;
    sendButton.style.opacity = state ? '0.5' : '1';
    sendButton.style.cursor = state ? 'not-allowed' : 'pointer';
    
    // Input field
    userInput.disabled = state;
    userInput.style.opacity = state ? '0.5' : '1';
    userInput.placeholder = state ? 'AI思考中，請稍候...' : '請輸入您的問題...';
    
    // Stop button - 強制設定
    if (stopButton) {
        stopButton.style.display = state ? 'inline-block' : 'none';
        
        if (state) {
            // 強制移除所有可能導致問題的屬性
            stopButton.removeAttribute('disabled');
            stopButton.style.removeProperty('cursor');
            stopButton.style.opacity = '1';
            
            // 強制設定正確的樣式
            setTimeout(() => {
                stopButton.style.setProperty('cursor', 'pointer', 'important');
            }, 0);
        }
    }
}

    function stopAiThinking() {
        setAiThinking(false);
        if (controller) {
            controller.abort(); // stop request
        }
        setAiThinking(false);

        const loadingDiv = document.querySelector('.loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
        controller = null;
    }

    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    

    function parseAiMessage(message) {
    // 先處理換行符
    let parsed = message.replace(/\n/g, "<br>");
    
    // 匹配以 http 或 https 開頭的完整 URL
    parsed = parsed.replace(
        /(?<!href=["'])(https?:\/\/[^\s<>"'\n]+)/g,
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );

    return parsed;
}
    function addAIMessage(message,matchedTool = null) {

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai-message';
        let content = `<div class="ai-message-content">${parseAiMessage(message)}</div>`;
        console.log('matchedTools:', matchedTool);
        if (matchedTool && Array.isArray(matchedTool) && matchedTool.length > 0) {// 如果有匹配的工具和視頻URL
            content +=  `<div class="ai-video-content">`

            matchedTool.forEach(tool => {
                if(tool.videoUrl && tool.text && tool.text.trim() !== ''&& tool.text !== 'undefined'){
                    content += `
                        <button class="video-btn"
                            data-video-url="${tool.videoUrl}"
                            data-tool-name="${tool.name}" 
                            style="
                            background-color: #1c4479ff;
                            color: white;
                            margin: 5px;
                            border: none;
                            border-radius: 20px;
                            padding: 10px 20px;
                            margin-left: 10px;
                            cursor: pointer;
                            font-size: 1rem;
                            transition: all 0.3s ease;">
                            🎞️觀看 ${tool.name} 教學視頻
                        </button>&nbsp;&nbsp;&nbsp;
                        <button class="text-btn"
                            data-tool-name="${tool.name}" 
                            data-tool-text="${tool.text}" 
                            style="
                            
                            background-color: #1c4479ff;
                            color: white;
                            margin: 5px;
                            border: none;
                            border-radius: 20px;
                            padding: 10px 20px;
                            margin-left: 10px;
                            cursor: pointer;
                            font-size: 1rem;
                            transition: all 0.3s ease;">
                            📜查看 ${tool.name} 文字指示
                        </button>`;
                }
            });
            content += `</div>`;
            console.log('Message add to DOM');
        }
        messageDiv.innerHTML = content;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // 動態綁定事件
        const videoBtn = messageDiv.querySelectorAll('.video-btn');
        videoBtn.forEach(videoBtn => {
            videoBtn.addEventListener('click', function() {
                showVideo(
                    videoBtn.getAttribute('data-video-url'),
                    videoBtn.getAttribute('data-tool-name')
                );
            });
        });
        const textBtn = messageDiv.querySelectorAll('.text-btn');
        textBtn.forEach(textBtn => {
            textBtn.addEventListener('click', function() {
                addTextMessage(
                    textBtn.getAttribute('data-tool-name'),
                    textBtn.getAttribute('data-tool-text')
                );
            });
        });
    }

    function addTextMessage(toolName,toolText){
        console.log('addTextMessage called',{toolName,toolText});
        if(!toolText || toolText.trim() === '' || toolText === 'undefined'){
            alert("No text!!!");
            return; // Stop execution if no text
        }

        const textContainer = document.createElement('div');
        textContainer.className = 'chat-text-container'; // 
        textContainer.style.cssText = `position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;
        textContainer.innerHTML = `
         
          <div style="
            position: 
            background: white;
            width: 80%;
            max-width: 800px;
            height: 80%;
            max-height: 600px;
            border-radius: 10px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        ">
            <div style="padding: 15px; background: #f5f5f5; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; height: 60px;">
                <h3 style="margin: 0; color: #333; font-size: 1rem;">${toolName}</h3>
                <button class="close-text-btn" style="background: rgba(255, 255, 255, 1); color: rgb(0, 0, 0); border: none; padding: 5px 10px; cursor: pointer; border-radius: 3px;">
                    ✕ 關閉
                </button>
            </div>
            <div class="text-content-scroll" style="
                height: calc(100% - 60px);
                overflow-y: auto;
                padding: 20px;
                background: white;
                line-height: 1.6;
                font-size: 1rem;
                color: #333;
            ">
                <p>${toolText}</p>
            </div>
        </div>
        `;
        
      
        document.body.appendChild(textContainer);
        document.body.style.overflow = 'hidden';

        function closeTextModal() {
            textContainer.remove();
            document.body.style.overflow = '';
        }
        // 關閉按鈕事件
        const closeBtn = textContainer.querySelector('.close-text-btn');
        closeBtn.addEventListener('click', closeTextModal);

        // 點擊背景關閉
        textContainer.addEventListener('click', function(e) {
            if (e.target === textContainer) {
                closeTextModal();
            }
        });
        
}
    
    function addVideoMessage(videoUrl, toolName) {
        const videomodel = document.createElement('div');
        videomodel.className = 'video-modal'; // 改為更明確的類名
        videomodel.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        `;
        
        videomodel.innerHTML = `
            <div style="padding: 15px; background: #f5f5f5; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; height: 60px;">
                <button class="close-btn" style="position: absolute; top: 10px; right: 10px; z-index: 1001; background: rgba(255, 255, 255, 1); color: rgb(0, 0, 0); border: none; padding: 5px 10px; cursor: pointer;">
                    ✕ 關閉
                </button>
                <iframe 
                    src="${videoUrl}" 
                    width="100%" 
                    height="100%" 
                    frameborder="0" 
                    allow="autoplay; clipboard-write; picture-in-picture" 
                    allowfullscreen>
                </iframe>
                <p class="video-title" style="position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.7); color: white; padding: 8px; margin: 0;"><strong>${toolName}</strong></p>
            </div>
        `;
        
        document.body.appendChild(videomodel);
        document.body.style.overflow = 'hidden';

        // 關閉按鈕事件
        const closeBtn = videomodel.querySelector('.close-btn');
        closeBtn.addEventListener('click', closeVideoModal);

        const contentWrapper = document.querySelector('.content-wrapper');
        contentWrapper.appendChild(textSection);

        textSection.innerHTML = '';
        textSection.appendChild(textContainer);
        
        // 綁定關閉按鈕事件
        const closeTextBtn = textContainer.querySelector('.close-text-btn');
        closeTextBtn.addEventListener('click', () => {
            // 關閉時移除整個 text-section
            textSection.remove();
    });
        
        // // 點擊背景關閉
        // videomodel.addEventListener('click', function(e) {
        //     if (e.target === videomodel) {
        //         closeVideoModal();
        //     }
        // });

        // function closeVideoModal() {
        //     videomodel.remove();
        //     document.body.style.overflow = '';
        // }
    }
        
    function getTagMap(tag){
        const tagMap = {
            "text": "文字",
            "code": "代碼",
            "photo": "圖片",
            "audio": "音頻",
            "data-analyse": "數據分析",
            "video": "視頻",
        };
        return tagMap[tag] || tag;

    }

    function renderCard(cardData) {
        const container = document.getElementById("resourcesContainer");
        if (!container) {
            console.error("找不到 resourcesContainer 元素");
            return;
        }

        container.innerHTML = ''; // 清空容器
        
        cardData.forEach(cardInfo => {
            const card = document.createElement("div");
            card.className = "card";
            const videoContainerId = `videoContainer-${cardInfo.id}`;      
               
            // ensure cardInfo has the required properties
            if (!cardInfo.name || !cardInfo.description) {
                console.warn("卡片資料不完整:", cardInfo);
                return;
            }

            card.innerHTML = `
                <div class="card-image">
                    <img src="${cardInfo.icon || 'default-icon.png'}" 
                         alt="${cardInfo.name}"
                         onerror="this.src='default-icon.png'">
                </div>
                <div class="card-content">
                    <h3>${cardInfo.name}</h3>
                    <h5><strong>介紹</strong></h5>
                    <p>${cardInfo.description}</p><br>
                    <h5><strong>限制</strong></h5>
                    <p>${cardInfo.limitations}</p>
                    <div class="tags">
                        ${cardInfo.tags?.map(tag => `
                            <span class="tag">${getTagMap(tag)}</span>
                        `).join('') || ''}
                    </div>
                    <div class="buttons">
                        <button class="video-toggle-button" data-video-id="${videoContainerId}" data-video-url ="${cardInfo.videoUrl || ''}" data-tool-name="${cardInfo.name}">
                            觀看視頻
                        </button>
                        <a href="${cardInfo.website || '#'}" 
                           target="_blank" 
                           class="button">
                            訪問網站
                        </a>
                    </div>
                    <div class="video-container" id ="${videoContainerId}" style="display: none;">
                    </div>
                </div>
            `;
            // card.querySelector('.video-container').style.display = 'none'; // 隱藏卡
            container.appendChild(card);
            const btn = card.querySelector('.video-toggle-button');
            const videoContainer = card.querySelector(".video-container");
            let isVideoPlaying = false;
            btn.addEventListener('click', () => {
                const videoUrl = btn.dataset.videoUrl || DEFAULT_VIDEO_URL;
                const toolName = btn.dataset.toolName || '';
                if (!isVideoPlaying) {
                    videoContainer.innerHTML = `
                        <iframe src="${videoUrl}"
                            width="100%"
                            height="300"
                            frameborder="0"
                            allow="autoplay; clipboard-write; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                        <p class="video-title"><strong>${toolName}</strong></p>
                    `;
                    videoContainer.style.display = 'block';
                    btn.textContent = "關閉視頻";
                    isVideoPlaying = true;
                } else {
                    videoContainer.innerHTML = '';
                    videoContainer.style.display = 'none';
                    btn.textContent = "觀看視頻";
                    isVideoPlaying = false;
                }
            })
        });
        
    }
    
    function filterCards(tag){
        const tags = document.querySelectorAll(".tag-button");
        tags.forEach(t => {t.classList.remove("active")});
        document.querySelector(`.tag-button[data-tag="${tag}"]`).classList.add("active");
        if (tag === "all") {
            renderCard(aiInfos);
            return
        }
        const filteredCards = aiInfos.filter(card => card.tags.includes(tag));
        renderCard(filteredCards);
    }

    document.addEventListener("DOMContentLoaded", () => {
        const tags = document.querySelectorAll(".tag-button");
        tags.forEach(tag => {
            tag.addEventListener("click", () => {
                filterCards(tag.dataset.tag);
            });
            tag.addEventListener("keypress", (e) => {
                if (e.key === "Enter") {
                    filterCards(tag.dataset.tag);
                }
            
            });
        });
    },
    );

    function showVideo(videoUrl, toolName) {
        // 先檢查是否已有視頻容器，如果有就移除
        const existingVideoContainer = document.querySelector('.chat-video-container');
        if (existingVideoContainer) {
            existingVideoContainer.remove();
        }
        
        // 創建視頻容器
        const videoContainer = document.createElement('div');
        videoContainer.className = 'chat-video-container';
        
        videoContainer.innerHTML = `
            <div style="padding: 15px; background: #f5f5f5; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; height: 60px;">
                <h4 style="margin: 0; color: #333; font-size: 1rem;">${toolName} 教學視頻</h4>
                <button class="close-video-btn" style="background: #ffffffff; color: black; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer;">
                    ✕ 
                </button>
            </div>
            <div style="height: calc(100% - 60px);">
                <iframe 
                    src="${videoUrl}"
                    style="width: 100%; height: 100%;"
                    frameborder="0"
                    allow="autoplay; clipboard-write; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
        `;
        
        // 檢查是否已有 video-section，如果沒有就創建
        let videoSection = document.querySelector('.video-section');
        if (!videoSection) {
            videoSection = document.createElement('div');
            videoSection.className = 'video-section';
            
            // 將 video-section 插入到 content-wrapper 中
            const contentWrapper = document.querySelector('.content-wrapper');
            contentWrapper.appendChild(videoSection);
        }
        
        // 將視頻容器插入到 video-section 中
        videoSection.innerHTML = '';
        videoSection.appendChild(videoContainer);
        
        // 綁定關閉按鈕事件
        const closeBtn = videoContainer.querySelector('.close-video-btn');
        closeBtn.addEventListener('click', () => {
            // 關閉時移除整個 video-section
            videoSection.remove();
        });
    }
    
