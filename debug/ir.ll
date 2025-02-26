; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

@"true" = constant i1 1
@"false" = constant i1 0
define i32 @"add"(i32 %".1", i32 %".2")
{
add_entry:
  %".4" = alloca i32
  store i32 %".1", i32* %".4"
  %".6" = alloca i32
  store i32 %".2", i32* %".6"
  %".8" = load i32, i32* %".4"
  %".9" = load i32, i32* %".6"
  %".10" = add i32 %".8", %".9"
  ret i32 %".10"
}

define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 0, i32* %".2"
  %".4" = alloca i32
  store i32 0, i32* %".4"
  br label %"for_loop_entry_1"
for_loop_entry_1:
  %".7" = load i32, i32* %".4"
  %".8" = icmp eq i32 %".7", 1
  br i1 %".8", label %"for_loop_entry_1.if", label %"for_loop_entry_1.endif"
for_loop_otherwise_1:
  %".35" = load i32, i32* %".2"
  ret i32 %".35"
for_loop_entry_1.if:
  %".10" = load i32, i32* %".4"
  %".11" = call i32 @"add"(i32 %".10", i32 8)
  %".12" = alloca [12 x i8]*
  store [12 x i8]* @"__str_2", [12 x i8]** %".12"
  %".14" = bitcast [12 x i8]* @"__str_2" to i8*
  %".15" = call i32 (i8*, ...) @"printf"(i8* %".14", i32 %".11")
  br label %"for_loop_entry_1.endif"
for_loop_entry_1.endif:
  %".17" = load i32, i32* %".4"
  %".18" = icmp eq i32 %".17", 5
  br i1 %".18", label %"for_loop_entry_1.endif.if", label %"for_loop_entry_1.endif.endif"
for_loop_entry_1.endif.if:
  br label %"for_loop_otherwise_1"
for_loop_entry_1.endif.endif:
  %".21" = load i32, i32* %".4"
  %".22" = alloca [9 x i8]*
  store [9 x i8]* @"__str_3", [9 x i8]** %".22"
  %".24" = bitcast [9 x i8]* @"__str_3" to i8*
  %".25" = call i32 (i8*, ...) @"printf"(i8* %".24", i32 %".21")
  %".26" = load i32, i32* %".4"
  %".27" = load i32, i32* %".2"
  store i32 %".26", i32* %".2"
  %".29" = load i32, i32* %".4"
  %".30" = add i32 %".29", 1
  store i32 %".30", i32* %".4"
  %".32" = load i32, i32* %".4"
  %".33" = icmp slt i32 %".32", 10
  br i1 %".33", label %"for_loop_entry_1", label %"for_loop_otherwise_1"
}

@"__str_2" = internal constant [12 x i8] c"i + 8: %i\0a\00\00"
@"__str_3" = internal constant [9 x i8] c"i = %i\0a\00\00"