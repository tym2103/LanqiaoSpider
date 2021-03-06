import os
import re

from config import problem_save_path, problem_mysql_save_path
from utils import mongo_util
from utils.file_util import clone_all_files
from utils.mysql.mysql_db import *
from utils.mongo_util import *


def get_format_problem(problem, name_list):
    """
    get a format problem data set to insert or update to mysql
    :param problem:
    :param name_list: insert or update to mysql columns value
    :return:
    """
    # change time_limit unit s to ms
    time_limit = problem.get(Problem.TIME_LIMIT)
    time_limit = str(int(float(time_limit) * 1000))
    problem[Problem.TIME_LIMIT] = time_limit
    # print(problem[PROBLEM.TIME_LIMIT])
    # problem_id
    insert_problem = []
    # insert_problem.append()
    for idx in name_list:
        if idx == Problem.ID:
            # need string
            insert_problem.append(get_insert_problem_id())
            continue
        elif idx == Problem.USER_ID:
            insert_problem.append(1)
            continue
        info = problem.get(idx, "")
        info = deal_text_format(info)
        # only json string need
        insert_problem.append(info)
    return insert_problem


def inset_to_mysql(problem):
    insert_problem = get_format_problem(problem, [Problem.ID, Problem.USER_ID, Problem.TITLE, Problem.TAG,
                                                  Problem.DESCRIPTION, Problem.FORMAT_INPUT, Problem.FORMAT_OUTPUT,
                                                  Problem.SAMPLE_INPUT, Problem.SAMPLE_OUTPUT, Problem.HINT,
                                                  Problem.MEMORY_LIMIT, Problem.TIME_LIMIT])
    # SQL 插入语句
    sql = """
        INSERT INTO problem(problem_id,user_id,title,tag,description,
    format_input,format_output,sample_input,sample_output,hint,
    memory_limit,time_limit) 
    VALUES(%d,%d,'%s','%s','%s','%s','%s','%s','%s','%s',%s,%s)
        """ % tuple(insert_problem)
    # print(sql)
    try:
        # 执行sql语句
        mysql_cursor.execute(sql)
        # 提交到数据库执行
        mysql_db.commit()
    except:
        # print(sql)
        print("sql error")
        traceback.print_exc()
        # 如果发生错误则回滚
        mysql_db.rollback()
    # check if insert success
    mysql_id = insert_problem[0]
    if find_in_mysql_with_id(mysql_id):
        clone_problem_data(mysql_id, problem[Problem.ID])
        update_mongodb(problem, mysql_id=mysql_id)
    else:
        print("not find problem with problem id = %d" % mysql_id)


def get_insert_problem_id():
    # SQL 查询语句
    sql = "SELECT max(problem_id) FROM problem where problem_id"
    try:
        # 执行SQL语句
        mysql_cursor.execute(sql)
        # 获取所有记录列表
        result = mysql_cursor.fetchone()
        # 有可能一个都没有, None
        max_id = result[0]
        if not max_id:
            return 1000
        else:
            return max_id + 1
    except:
        traceback.print_exc()
        print("Error: unable to fetch data")


def find_in_mysql_with_id(id):
    # SQL 查询语句
    sql = "SELECT * FROM problem where problem_id = '%s'" % (id)
    try:
        # 执行SQL语句
        mysql_cursor.execute(sql)
        # 获取所有记录列表
        results = mysql_cursor.fetchall()
        # print(results)
        return results
    except:
        traceback.print_exc()
        print("Error: unable to fetch data")


def find_in_mysql_with_title(title):
    # SQL 查询语句
    sql = "SELECT * FROM problem where title = '%s'" % (title)
    try:
        # 执行SQL语句
        mysql_cursor.execute(sql)
        # 获取所有记录列表
        results = mysql_cursor.fetchall()
        # print(results)
        return results
    except:
        traceback.print_exc()
        print("Error: unable to fetch data")


def deal_text_format(text):
    text = text.replace(r"'", r"\'", re.S)
    return text


def update_info_mysql(problem):
    format_problem = get_format_problem(problem, [Problem.DESCRIPTION, Problem.FORMAT_INPUT, Problem.FORMAT_OUTPUT,
                                                  Problem.SAMPLE_INPUT, Problem.SAMPLE_OUTPUT, Problem.HINT,
                                                  Problem.TITLE])
    # SQL 查询语句
    sql = """UPDATE problem set 
    description = '%s',
    format_input = '%s' ,
    format_output = '%s', 
    sample_input = '%s', 
    sample_output = '%s' ,
    hint = '%s'
    where title = '%s'""" % tuple(format_problem)
    # print(sql)
    title = problem[Problem.TITLE]
    try:
        # 执行SQL语句
        mysql_cursor.execute(sql)
        # 提交到数据库执行
        mysql_db.commit()
        print("{} update successful".format(title))
        return True
    except:
        # 发生错误时回滚
        # print(sql)
        print("{} update fail".format(title))
        mysql_db.rollback()
        return False


def update_problem_id(new_id, old_id):
    # return
    # SQL 查询语句
    sql = """UPDATE problem set problem_id = %s where problem_id = %s""" % (new_id, old_id)
    # print(sql)
    try:
        # 执行SQL语句
        mysql_cursor.execute(sql)
        # 提交到数据库执行
        mysql_db.commit()
        # print("{} update successful".format(title))
    except:
        # 发生错误时回滚
        # print(sql)
        mysql_db.rollback()


def update_problem_data(problem):
    format_problem = get_format_problem(problem, [Problem.DATA, Problem.TITLE])
    if problem[Problem.TITLE] == "瓷砖铺放":
        print(format_problem)
        # return
    # SQL 查询语句
    sql = """UPDATE problem set 
        judge_data = '%s'
        where title = '%s'""" % tuple(format_problem)
    # print(sql)
    title = problem[Problem.TITLE]
    try:
        # 执行SQL语句
        mysql_cursor.execute(sql)
        # 提交到数据库执行
        mysql_db.commit()
        print("{} update successful".format(title))
        return True
    except:
        # 发生错误时回滚
        # print(sql)
        print("{} update fail".format(title))
        mysql_db.rollback()
        return False


def clone_problem_data(mysql_id, problem_id):
    """
    clone problem data form download with problem_id as directory name
    :return:
    """
    source_dir = problem_save_path + "/" + problem_id
    target_dir = problem_mysql_save_path + "/" + str(mysql_id)
    shutil.copytree(source_dir, target_dir)


def update_mongodb(problem, mysql_id):
    problem[Problem.MYSQL_ID] = mysql_id
    mongo_util.problem_collection. \
        update_one({Problem.ID: problem[Problem.ID]}, {"$set": {Problem.MYSQL_ID: mysql_id}})


def main():
    # 重新开始记得，清空关联mysql_id
    # problem_collection.update_many({}, {"$set": {Problem.MYSQL_ID: ""}})
    # 按照一定的顺序
    for begin_prefix in tag_dict.values():
        id_reg = {"$regex": "^" + begin_prefix}
        query = {Problem.ID: id_reg, Problem.DATA_STATUS: StateValue.FILE_SUCCESS}
        problems = problem_collection.find(query).sort(Problem.ID)
        for problem in problems:
            print(problem[Problem.ID])
            title = problem[Problem.TITLE]
            mysql_id = problem.get(Problem.MYSQL_ID)
            # maybe mysql field == ""
            find_problem = find_in_mysql_with_id(problem[Problem.MYSQL_ID])
            if find_problem:
                print("{%s} is already in mysql table" % title)
            else:
                inset_to_mysql(problem)
                print("{} inserts in mysql table".format(title))
    total = problem_collection.count_documents({Problem.DATA_STATUS: StateValue.FILE_SUCCESS})
    print("total download file success = {}".format(total))
    mysql_db.close()


if __name__ == "__main__":
    main()