; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

%"Person" = type {i8*, i8*, i64}
declare i64 @"printf"(i8* %".1", ...)

declare i64 @"scanf"(i8* %".1", ...)

@"true" = constant i1 1
@"false" = constant i1 0
define %"Person" @"Person_init"()
{
Person_init_entry:
  %".2" = insertvalue %"Person" zeroinitializer, i8* null, 0
  %".3" = insertvalue %"Person" %".2", i8* null, 1
  %".4" = insertvalue %"Person" %".3", i64 0, 2
  ret %"Person" %".4"
}

define void @"Person_greet"(%"Person" %".1", i8* %".2")
{
Person_greet_entry:
  %".4" = alloca i8*
  store i8* %".2", i8** %".4"
  %".6" = getelementptr [18 x i8], [18 x i8]* @"__str_1", i32 0, i32 0
  %".7" = load i8*, i8** %".4"
  %".8" = extractvalue %"Person" %".1", 0
  %".9" = extractvalue %"Person" %".1", 1
  %".10" = alloca i8*
  store i8* %".6", i8** %".10"
  %".12" = bitcast [18 x i8]* @"__str_1" to i8*
  %".13" = call i64 (i8*, ...) @"printf"(i8* %".12", i8* %".7", i8* %".8", i8* %".9")
  %".14" = getelementptr [21 x i8], [21 x i8]* @"__str_2", i32 0, i32 0
  %".15" = extractvalue %"Person" %".1", 2
  %".16" = alloca i8*
  store i8* %".14", i8** %".16"
  %".18" = bitcast [21 x i8]* @"__str_2" to i8*
  %".19" = call i64 (i8*, ...) @"printf"(i8* %".18", i64 %".15")
  ret void
}

@"__str_1" = internal constant [18 x i8] c"%s, I am %s %s.\0a\00\00"
@"__str_2" = internal constant [21 x i8] c"I am %i years old.\0a\00\00"
define i64 @"main"()
{
main_entry:
  %".2" = call %"Person" @"Person_init"()
  %".3" = getelementptr [14 x i8], [14 x i8]* @"__str_3", i32 0, i32 0
  %".4" = alloca i8*
  store i8* %".3", i8** %".4"
  %".6" = bitcast [14 x i8]* @"__str_3" to i8*
  %".7" = call i64 (i8*, ...) @"printf"(i8* %".6")
  %".8" = getelementptr [1 x i8], [1 x i8]* @"__str_4", i32 0, i32 0
  %".9" = alloca i8*
  store i8* getelementptr ([1 x i8], [1 x i8]* @"name_str", i32 0, i32 0), i8** %".9"
  %".11" = getelementptr [3 x i8], [3 x i8]* @"__str_5", i32 0, i32 0
  %".12" = load i8*, i8** %".9"
  %".13" = bitcast [3 x i8]* @"__str_5" to i8*
  %".14" = call i64 (i8*, ...) @"scanf"(i8* %".13", i8* %".12")
  %".15" = extractvalue %"Person" %".2", 0
  %".16" = load i8*, i8** %".9"
  %".17" = insertvalue %"Person" %".2", i8* %".16", 0
  %".18" = extractvalue %"Person" %".17", 1
  %".19" = getelementptr [6 x i8], [6 x i8]* @"__str_6", i32 0, i32 0
  %".20" = insertvalue %"Person" %".17", i8* %".19", 1
  %".21" = extractvalue %"Person" %".20", 2
  %".22" = insertvalue %"Person" %".20", i64 21, 2
  %".23" = getelementptr [6 x i8], [6 x i8]* @"__str_7", i32 0, i32 0
  call void @"Person_greet"(%"Person" %".22", i8* %".23")
  ret i64 0
}

@"__str_3" = internal constant [14 x i8] c"Your name ?\0a\00\00"
@"__str_4" = internal constant [1 x i8] c"\00"
@"name_str" = constant [1 x i8] c"\00"
@"__str_5" = internal constant [3 x i8] c"%s\00"
@"__str_6" = internal constant [6 x i8] c"Rucar\00"
@"__str_7" = internal constant [6 x i8] c"Hello\00"