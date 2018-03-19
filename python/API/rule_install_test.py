def switch_deploy(dp, sw_rule, bdid, step=1):
    filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
    table_id = 0
    script_init(filepath)
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    for r in sw_rule['del']:
        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "delete_strict"))
    for r in sw_rule['add']:
        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
    subprocess.Popen("%s" %filepath)


if __name__ == '__main__':
