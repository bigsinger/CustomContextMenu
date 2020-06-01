

function main(cmdname, file, isMultiFiles)
	cmdname = cmdname or 'nil'
	file = file or 'nil'
	isMultiFiles = isMultiFiles or 'false'
	print('cmd name: '..cmdname..'\nfile: '..file..'\nisMultiFiles: '..isMultiFiles)
	os.execute('pause')
	return 1
end

return main(...)