function main(cmdid, cmdname, file, isMultiFiles)
	cmdid = cmdid or 'nil'
	cmdname = cmdname or 'nil'
	file = file or 'nil'
	isMultiFiles = isMultiFiles or 'false'
	print('cmdid: '..cmdid..' cmd name: '..cmdname..'\nfile: '..file..'\nisMultiFiles: '..isMultiFiles)
	cmds = string.format('python ./plug/oncommand.py %s \"%s\"', cmdname, file)
	if isMultiFiles then cmds = cmds..' '..isMultiFiles end
	os.execute(cmds)
	--os.execute('pause')
	return 1
end

return main(...)