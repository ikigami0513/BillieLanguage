; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

@"true" = constant i1 1
@"false" = constant i1 0
define i32 @"main"()
{
main_entry:
  %".2" = alloca [14 x i8]*
  store [14 x i8]* @"__str_1", [14 x i8]** %".2"
  %".4" = bitcast [14 x i8]* @"__str_1" to i8*
  %".5" = call i32 (i8*, ...) @"printf"(i8* %".4")
  ret i32 0
}

@"__str_1" = internal constant [14 x i8] c"Hello, World!\00"