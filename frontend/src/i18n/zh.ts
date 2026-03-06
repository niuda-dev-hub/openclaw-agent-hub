/** 中文翻译（默认语言） */
export const zh = {
    // 导航
    nav: {
        dashboard: '仪表盘',
        tasks: '任务',
        agents: 'Agent',
        leaderboard: '排行榜',
        admin: '管理后台',
    },
    // 通用
    common: {
        loading: '加载中...',
        error: '错误',
        cancel: '取消',
        confirm: '确认',
        create: '创建',
        assign: '指派',
        save: '保存',
        close: '关闭',
        back: '返回',
        refresh: '刷新',
        search: '搜索',
        noData: '暂无数据',
        count: '共 {n} 条',
        rawJson: '原始数据',
        enabled: '已启用',
        disabled: '已禁用',
    },
    // 状态
    status: {
        online: '在线',
        idle: '空闲',
        offline: '离线',
        draft: '草稿',
        open: '开放',
        running: '进行中',
        finalized: '已完成',
        cancelled: '已取消',
        queued: '排队中',
        finished: '已完成',
        failed: '失败',
    },
    // 仪表盘
    dashboard: {
        title: '仪表盘',
        totalTasks: '任务总数',
        runningTasks: '进行中',
        finalizedTasks: '已完成',
        onlineAgents: '在线 Agent',
        recentTasks: '最近任务',
    },
    // 任务
    tasks: {
        title: '任务列表',
        createTask: '创建任务',
        searchPlaceholder: '搜索标题/ID/状态',
        colTitle: '标题',
        colStatus: '状态',
        colCreated: '创建时间',
        colId: 'ID',
        open: '查看',
        updated: '更新：',
    },
    // 任务创建表单
    createTask: {
        title: '创建新任务',
        fieldTitle: '任务标题',
        fieldTitlePlaceholder: '输入任务标题',
        fieldPrompt: '任务描述（Prompt）',
        fieldPromptPlaceholder: '详细描述任务要求...',
        fieldOutputType: '预期输出类型',
        outputTypeText: '文本',
        outputTypeCode: '代码',
        outputTypeFile: '文件',
        fieldCreatedBy: '发布人',
        fieldCreatedByPlaceholder: '你的名字或 ID（可选）',
    },
    // 任务详情
    taskDetail: {
        title: '任务详情',
        assignAgent: '指派 Agent',
        startTask: '启动任务',
        submissions: '提交产物',
        evaluations: '评分',
        decision: '终审结果',
        events: '审计事件',
        participants: '参与者',
        submissionCount: '共 {n} 个提交',
        evalCount: '共 {n} 个评分',
        noDecision: '暂无终审结果',
        noEvents: '暂无事件',
        noSubmissions: '暂无提交',
        noEvaluations: '暂无评分',
        promptLabel: '任务描述',
    },
    // 指派 Agent
    assignTask: {
        title: '指派 Agent',
        selectAgent: '选择 Agent',
        noAgentsAvailable: '暂无可用 Agent',
        assignedSuccess: '指派成功',
    },
    // Agent 管理
    agents: {
        title: 'Agent 管理',
        registerAgent: '注册 Agent',
        colName: '名称',
        colType: '类型',
        colStatus: '状态',
        colLastSeen: '最近心跳',
        colActions: '操作',
        enable: '启用',
        disable: '停用',
        neverSeen: '从未上报',
        description: '描述',
        activeTasks: '当前任务',
        noActiveTasks: '无',
    },
    // 排行榜
    leaderboard: {
        title: '全局排行榜',
        colAgent: 'Agent',
        colAvgScore: '平均分',
        colReviews: '评审次数',
        colTask: '任务',
        noData: '暂无评分数据',
    },
    // 管理后台
    admin: {
        title: '管理后台',
        tasks: '任务管理',
        runs: 'Run 列表',
        submissions: '提交管理',
        colTitle: '标题',
        colStatus: '状态',
        colCreated: '时间',
        colActions: '操作',
        finalize: 'Finalize',
    },
    // 主题
    theme: {
        label: '主题',
        office: '办公白',
        dark: '深色',
    },
    // 语言
    language: {
        label: '语言',
        zh: '中文',
        en: 'English',
    },
}

export type Translations = typeof zh
