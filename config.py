def config():
	db = parse_dsn("postgres://roknlgitfflwen:51aa0c1f9e6fbb9d4feb05701092f6c512a09939579e53c66f60cbfd82fcd589@ec2-54-208-11-146.compute-1.amazonaws.com:5432/d74g7dumg8dmnl")
	else:
		raise Exception(
			flash('param is not found in the file')
	return db