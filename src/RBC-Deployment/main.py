import sys
import os


# inputData 算法入参  relPath:相对路径    logger：日志打印对象，打印的日志可被算法平台抓取（print方法抓取不了）
def execute(inputData, relPath, logger):
    # 使用相对路径引用主算法程序，主程序中引用无需再用相对路径
    main_file_path = os.path.abspath(__file__)
    main_directory = os.path.dirname(main_file_path)

    # 判断执行是否成功，以约定的格式和枚举状态返回 成功：success 失败：fail 可预见的有意义的失败一般包装为成功以便上层应用处理
    try:
        # info 和error只是日志级别的区别，不中断算法执行
        logger.info("logger.info打印出的日志")
        logger.error("logger.error打印出的日志")
        sys.path.append(main_directory)
        import controller_RBC
        import Data2DB
        # 由于是多个设备,需确定设备索引值
        item_dir = Data2DB.get_item(inputData)

        # 调用RBC算法
        result, Weather_dir = controller_RBC.rbc(inputData, logger, item_dir)

        # 存入数据库
        Data2DB.data_write_db(inputData, result, logger, item_dir, Weather_dir)

        return {"status": "success", "data": result, "msg": "msg"}
    except Exception as errormsg:
        return {"status": "fail", "msg": str(errormsg), "data": "null"}
