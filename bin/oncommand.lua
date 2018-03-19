

function main(thispath, cmdid, cmdname, file, isMultiFiles)
	cmdid = cmdid or 'nil'
	cmdname = cmdname or 'nil'
	file = file or 'nil'
	isMultiFiles = isMultiFiles or 'false'
	print('cmd id: '..cmdid..' cmd name: '..cmdname..'\nfile: '..file..'\nisMultiFiles: '..isMultiFiles)
	cmds = string.format('python \"%splug/oncommand.py\" %s \"%s\"', thispath, cmdname, file)
	if isMultiFiles then
		cmds = cmds..' '..isMultiFiles
	end
	os.execute(cmds)
	--os.execute('pause')
	return 1
end

return main(...)