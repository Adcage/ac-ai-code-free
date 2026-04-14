package com.adcage.acaicodefree.service.impl;

import cn.hutool.core.bean.BeanUtil;
import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.RandomUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONUtil;
import com.adcage.acaicodefree.common.ErrorCode;
import com.adcage.acaicodefree.constant.AppConstant;
import com.adcage.acaicodefree.core.AiCodeGeneratorFacade;
import com.adcage.acaicodefree.exception.BusinessException;
import com.adcage.acaicodefree.exception.ThrowUtils;
import com.adcage.acaicodefree.mapper.ChatHistoryMapper;
import com.adcage.acaicodefree.mapper.ChatSessionMapper;
import com.adcage.acaicodefree.model.dto.chat.ChatHistoryQueryRequest;
import com.adcage.acaicodefree.model.enums.CodeGenTypeEnum;
import com.adcage.acaicodefree.model.dto.app.AppQueryRequest;
import com.adcage.acaicodefree.model.entity.ChatHistory;
import com.adcage.acaicodefree.model.entity.ChatSession;
import com.adcage.acaicodefree.model.entity.User;
import com.adcage.acaicodefree.model.vo.app.AppVO;
import com.adcage.acaicodefree.model.vo.chat.ChatHistoryVO;
import com.adcage.acaicodefree.model.vo.chat.ChatSessionVO;
import com.adcage.acaicodefree.model.vo.user.UserVO;
import com.mybatisflex.core.paginate.Page;
import com.adcage.acaicodefree.service.UserService;
import com.mybatisflex.core.query.QueryWrapper;
import com.mybatisflex.spring.service.impl.ServiceImpl;
import com.adcage.acaicodefree.model.entity.App;
import com.adcage.acaicodefree.mapper.AppMapper;
import com.adcage.acaicodefree.service.AppService;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

import java.io.File;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 应用 服务层实现。
 *
 * @author adcage
 */
@Service
public class AppServiceImpl extends ServiceImpl<AppMapper, App> implements AppService {

    private final UserService userService;
    private final AiCodeGeneratorFacade aiCodeGeneratorFacade;
    private final ChatSessionMapper chatSessionMapper;
    private final ChatHistoryMapper chatHistoryMapper;

    public AppServiceImpl(UserService userService,
                          AiCodeGeneratorFacade aiCodeGeneratorFacade,
                          ChatSessionMapper chatSessionMapper,
                          ChatHistoryMapper chatHistoryMapper) {
        this.userService = userService;
        this.aiCodeGeneratorFacade = aiCodeGeneratorFacade;
        this.chatSessionMapper = chatSessionMapper;
        this.chatHistoryMapper = chatHistoryMapper;
    }

    @Override
    public void validApp(App app, boolean add) {
        if (app == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR);
        }
        String appName = app.getAppName();
        String initPrompt = app.getInitPrompt();

        // 创建时，参数不能为空
        if (add) {
            ThrowUtils.throwIf(StrUtil.isBlank(appName), ErrorCode.PARAMS_ERROR, "应用名称不能为空");
            ThrowUtils.throwIf(StrUtil.isBlank(initPrompt), ErrorCode.PARAMS_ERROR, "初始化提示词不能为空");
        }
        // 有参数则校验
        if (StrUtil.isNotBlank(appName) && appName.length() > 80) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "应用名称过长");
        }
        if (StrUtil.isNotBlank(initPrompt) && initPrompt.length() > 8192) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "初始化提示词过长");
        }
    }

    @Override
    public QueryWrapper getQueryWrapper(AppQueryRequest appQueryRequest) {
        if (appQueryRequest == null) {
            throw new BusinessException(ErrorCode.PARAMS_ERROR, "请求参数为空");
        }
        Long id = appQueryRequest.getId();
        String appName = appQueryRequest.getAppName();
        String initPrompt = appQueryRequest.getInitPrompt();
        String codeGenType = appQueryRequest.getCodeGenType();
        String deployKey = appQueryRequest.getDeployKey();
        Integer priority = appQueryRequest.getPriority();
        Long userId = appQueryRequest.getUserId();
        String userName = appQueryRequest.getUserName();
        Boolean onlyFeatured = appQueryRequest.getOnlyFeatured();
        String sortField = appQueryRequest.getSortField();
        String sortOrder = appQueryRequest.getSortOrder();

        QueryWrapper queryWrapper = QueryWrapper.create()
                .eq("id", id)
                .eq("userId", userId)
                .eq("codeGenType", codeGenType)
                .eq("deployKey", deployKey)
                .eq("priority", priority)
                .like("appName", appName)
                .like("initPrompt", initPrompt);

        // 按用户名模糊搜索
        if (StrUtil.isNotBlank(userName)) {
            List<Long> userIds = userService.list(QueryWrapper.create().like("userName", userName))
                    .stream().map(User::getId).collect(Collectors.toList());
            if (CollUtil.isNotEmpty(userIds)) {
                queryWrapper.in("userId", userIds);
            } else {
                // 未匹配到用户，强行使结果为空
                queryWrapper.eq("id", -1L);
            }
        }

        // 精选应用查询（优先级大于0）
        if (onlyFeatured != null && onlyFeatured) {
            queryWrapper.gt("priority", 0);
            // 精选应用按优先级降序排列
            queryWrapper.orderBy("priority", false);
        } else {
            // 普通排序
            queryWrapper.orderBy(sortField, "ascend".equals(sortOrder));
        }

        return queryWrapper;
    }

    @Override
    public AppVO getAppVO(App app) {
        if (app == null) {
            return null;
        }
        AppVO appVO = new AppVO();
        BeanUtil.copyProperties(app, appVO);
        Long userId = app.getUserId();
        if(userId != null){
            User user = userService.getById(userId);
            UserVO userVO = userService.getUserVO(user);
            appVO.setUser(userVO);
        }
        return appVO;
    }

    @Override
    public List<AppVO> getAppVOList(List<App> appList) {
        if (CollUtil.isEmpty(appList)) {
            return new ArrayList<>();
        }
        // 批量获取用户信息，避免 N+1 查询问题
        Set<Long> userIds = appList.stream()
                .map(App::getUserId)
                .collect(Collectors.toSet());
        Map<Long, UserVO> userVOMap = userService.listByIds(userIds).stream()
                .collect(Collectors.toMap(User::getId, userService::getUserVO));
        return appList.stream().map(app -> {
            AppVO appVO = getAppVO(app);
            UserVO userVO = userVOMap.get(app.getUserId());
            appVO.setUser(userVO);
            return appVO;
        }).collect(Collectors.toList());
    }

    @Override
    public Flux<String> chatToGenCode(Long appId, Long sessionId, String message, User loginUser) {
        // 1. 参数校验
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        ThrowUtils.throwIf(sessionId == null || sessionId <= 0, ErrorCode.PARAMS_ERROR, "会话 ID 不能为空");
        ThrowUtils.throwIf(StrUtil.isBlank(message), ErrorCode.PARAMS_ERROR, "用户消息不能为空");
        // 2. 查询应用信息并校验权限
        App app = getAndCheckApp(appId, loginUser);
        // 3. 校验会话归属
        getAndCheckChatSession(sessionId, appId, loginUser);
        // 4. 保存用户消息
        saveHistoryMessage(sessionId, appId, loginUser.getId(), message, "user", "success", app.getCodeGenType(), 0, null);
        updateSessionSummary(sessionId);
        // 5. 获取应用的代码生成类型
        String codeGenTypeStr = app.getCodeGenType();
        CodeGenTypeEnum codeGenTypeEnum = CodeGenTypeEnum.getEnumByValue(codeGenTypeStr);
        if (codeGenTypeEnum == null) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "不支持的代码生成类型");
        }
        // 6. 调用 AI 生成代码并在流完成后落库 AI 消息
        StringBuilder assistantMessageBuilder = new StringBuilder();
        long startTime = System.currentTimeMillis();
        return aiCodeGeneratorFacade.generateAndSaveCodeStream(message, codeGenTypeEnum, appId)
                .doOnNext(assistantMessageBuilder::append)
                .doOnComplete(() -> {
                    int latencyMs = (int) (System.currentTimeMillis() - startTime);
                    String aiMessage = assistantMessageBuilder.toString();
                    saveHistoryMessage(sessionId, appId, loginUser.getId(), aiMessage, "ai", "success", codeGenTypeStr, latencyMs, null);
                    updateSessionSummary(sessionId);
                })
                .doOnError(error -> {
                    int latencyMs = (int) (System.currentTimeMillis() - startTime);
                    Map<String, String> extraInfo = Map.of("error", error.getMessage());
                    String aiMessage = StrUtil.isBlank(assistantMessageBuilder.toString())
                            ? "生成失败：" + error.getMessage()
                            : assistantMessageBuilder.toString();
                    saveHistoryMessage(sessionId, appId, loginUser.getId(), aiMessage, "ai", "failed", codeGenTypeStr, latencyMs, JSONUtil.toJsonStr(extraInfo));
                    updateSessionSummary(sessionId);
                });
    }

    @Override
    public Long createChatSession(Long appId, User loginUser) {
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        App app = getAndCheckApp(appId, loginUser);
        long sessionCount = chatSessionMapper.selectCountByQuery(QueryWrapper.create()
                .eq("appId", appId)
                .eq("userId", loginUser.getId()));
        String sessionTitle = "新会话 " + (sessionCount + 1);
        ChatSession chatSession = ChatSession.builder()
                .appId(appId)
                .userId(loginUser.getId())
                .title(sessionTitle)
                .messageCount(0)
                .modelName(app.getCodeGenType())
                .lastMessageTime(LocalDateTime.now())
                .build();
        int insertResult = chatSessionMapper.insert(chatSession);
        ThrowUtils.throwIf(insertResult <= 0 || chatSession.getId() == null, ErrorCode.OPERATION_ERROR, "创建会话失败");
        return chatSession.getId();
    }

    @Override
    public List<ChatSessionVO> listChatSession(Long appId, User loginUser) {
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        getAndCheckApp(appId, loginUser);
        QueryWrapper queryWrapper = QueryWrapper.create()
                .eq("appId", appId)
                .eq("userId", loginUser.getId())
                .orderBy("updateTime", false);
        return chatSessionMapper.selectListByQuery(queryWrapper).stream()
                .map(session -> {
                    ChatSessionVO chatSessionVO = new ChatSessionVO();
                    BeanUtil.copyProperties(session, chatSessionVO);
                    return chatSessionVO;
                })
                .collect(Collectors.toList());
    }

    @Override
    public Page<ChatHistoryVO> listChatHistoryByPage(ChatHistoryQueryRequest chatHistoryQueryRequest, User loginUser) {
        ThrowUtils.throwIf(chatHistoryQueryRequest == null, ErrorCode.PARAMS_ERROR);
        Long appId = chatHistoryQueryRequest.getAppId();
        Long sessionId = chatHistoryQueryRequest.getSessionId();
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        ThrowUtils.throwIf(sessionId == null || sessionId <= 0, ErrorCode.PARAMS_ERROR, "会话 ID 不能为空");
        int pageNum = Math.max(chatHistoryQueryRequest.getPageNum(), 1);
        int pageSize = Math.min(Math.max(chatHistoryQueryRequest.getPageSize(), 1), 50);
        getAndCheckApp(appId, loginUser);
        getAndCheckChatSession(sessionId, appId, loginUser);
        QueryWrapper queryWrapper = QueryWrapper.create()
                .eq("sessionId", sessionId)
                .eq("appId", appId)
                .eq("userId", loginUser.getId())
                .orderBy("seqNo", true);
        List<ChatHistory> allHistoryList = chatHistoryMapper.selectListByQuery(queryWrapper);
        int fromIndex = (pageNum - 1) * pageSize;
        if (fromIndex >= allHistoryList.size()) {
            return new Page<>(pageNum, pageSize, allHistoryList.size());
        }
        int toIndex = Math.min(fromIndex + pageSize, allHistoryList.size());
        List<ChatHistory> pageHistoryList = allHistoryList.subList(fromIndex, toIndex);
        List<ChatHistoryVO> records = pageHistoryList.stream().map(history -> {
            ChatHistoryVO chatHistoryVO = new ChatHistoryVO();
            BeanUtil.copyProperties(history, chatHistoryVO);
            return chatHistoryVO;
        }).collect(Collectors.toList());
        Page<ChatHistoryVO> resultPage = new Page<>(pageNum, pageSize, allHistoryList.size());
        resultPage.setRecords(records);
        return resultPage;
    }

    @Override
    public String deployApp(Long appId, User loginUser) {
        // 1. 参数校验
        ThrowUtils.throwIf(appId == null || appId <= 0, ErrorCode.PARAMS_ERROR, "应用 ID 不能为空");
        ThrowUtils.throwIf(loginUser == null, ErrorCode.NOT_LOGIN_ERROR, "用户未登录");
        // 2. 查询应用信息
        App app = this.getById(appId);
        ThrowUtils.throwIf(app == null, ErrorCode.NOT_FOUND_ERROR, "应用不存在");
        // 3. 验证用户是否有权限部署该应用，仅本人可以部署
        if (!app.getUserId().equals(loginUser.getId())) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限部署该应用");
        }
        // 4. 检查是否已有 deployKey
        String deployKey = app.getDeployKey();
        // 没有则生成 6 位 deployKey（大小写字母 + 数字）
        if (StrUtil.isBlank(deployKey)) {
            deployKey = RandomUtil.randomString(6);
        }
        // 5. 获取代码生成类型，构建源目录路径
        String codeGenType = app.getCodeGenType();
        String sourceDirName = codeGenType + "_" + appId;
        String sourceDirPath = AppConstant.CODE_OUTPUT_ROOT_DIR + File.separator + sourceDirName;
        // 6. 检查源目录是否存在
        File sourceDir = new File(sourceDirPath);
        if (!sourceDir.exists() || !sourceDir.isDirectory()) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "应用代码不存在，请先生成代码");
        }
        // 7. 复制文件到部署目录
        String deployDirPath = AppConstant.CODE_DEPLOY_ROOT_DIR + File.separator + deployKey;
        try {
            FileUtil.copyContent(sourceDir, new File(deployDirPath), true);
        } catch (Exception e) {
            throw new BusinessException(ErrorCode.SYSTEM_ERROR, "部署失败：" + e.getMessage());
        }
        // 8. 更新应用的 deployKey 和部署时间
        App updateApp = new App();
        updateApp.setId(appId);
        updateApp.setDeployKey(deployKey);
        updateApp.setDeployedTime(LocalDateTime.now());
        boolean updateResult = this.updateById(updateApp);
        ThrowUtils.throwIf(!updateResult, ErrorCode.OPERATION_ERROR, "更新应用部署信息失败");
        // 9. 返回可访问的 URL
        return String.format("%s/%s/", AppConstant.CODE_DEPLOY_HOST, deployKey);
    }

    private App getAndCheckApp(Long appId, User loginUser) {
        ThrowUtils.throwIf(loginUser == null || loginUser.getId() == null, ErrorCode.NOT_LOGIN_ERROR, "用户未登录");
        App app = this.getById(appId);
        ThrowUtils.throwIf(app == null, ErrorCode.NOT_FOUND_ERROR, "应用不存在");
        if (!app.getUserId().equals(loginUser.getId())) {
            throw new BusinessException(ErrorCode.NO_AUTH_ERROR, "无权限访问该应用");
        }
        return app;
    }

    private ChatSession getAndCheckChatSession(Long sessionId, Long appId, User loginUser) {
        QueryWrapper queryWrapper = QueryWrapper.create()
                .eq("id", sessionId)
                .eq("appId", appId)
                .eq("userId", loginUser.getId());
        ChatSession chatSession = chatSessionMapper.selectOneByQuery(queryWrapper);
        ThrowUtils.throwIf(chatSession == null, ErrorCode.NOT_FOUND_ERROR, "会话不存在");
        return chatSession;
    }

    private void saveHistoryMessage(Long sessionId, Long appId, Long userId, String message,
                                    String messageType, String status, String modelName,
                                    Integer latencyMs, String extra) {
        ChatHistory chatHistory = ChatHistory.builder()
                .sessionId(sessionId)
                .seqNo(getNextSeqNo(sessionId))
                .message(StrUtil.blankToDefault(message, ""))
                .messageType(messageType)
                .status(status)
                .appId(appId)
                .userId(userId)
                .modelName(modelName)
                .inputTokens(0)
                .outputTokens(0)
                .latencyMs(latencyMs)
                .extra(extra)
                .build();
        int insertResult = chatHistoryMapper.insert(chatHistory);
        ThrowUtils.throwIf(insertResult <= 0, ErrorCode.OPERATION_ERROR, "保存聊天记录失败");
    }

    private Integer getNextSeqNo(Long sessionId) {
        long count = chatHistoryMapper.selectCountByQuery(QueryWrapper.create().eq("sessionId", sessionId));
        return (int) (count + 1);
    }

    private void updateSessionSummary(Long sessionId) {
        ChatSession chatSession = chatSessionMapper.selectOneByQuery(QueryWrapper.create().eq("id", sessionId));
        if (chatSession == null) {
            return;
        }
        long count = chatHistoryMapper.selectCountByQuery(QueryWrapper.create().eq("sessionId", sessionId));
        chatSession.setMessageCount((int) count);
        chatSession.setLastMessageTime(LocalDateTime.now());
        chatSessionMapper.update(chatSession);
    }

}
