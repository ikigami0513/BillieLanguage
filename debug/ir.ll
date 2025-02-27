; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...)

@"true" = constant i1 1
@"false" = constant i1 0
define i32 @"factorial"(i32 %".1")
{
factorial_entry:
  %".3" = alloca i32
  store i32 %".1", i32* %".3"
  %".5" = load i32, i32* %".3"
  %".6" = icmp eq i32 %".5", 0
  %".7" = load i32, i32* %".3"
  %".8" = icmp eq i32 %".7", 1
  %".9" = or i1 %".6", %".8"
  br i1 %".9", label %"factorial_entry.if", label %"factorial_entry.endif"
factorial_entry.if:
  ret i32 1
factorial_entry.endif:
  %".12" = load i32, i32* %".3"
  %".13" = load i32, i32* %".3"
  %".14" = sub i32 %".13", 1
  %".15" = call i32 @"factorial"(i32 %".14")
  %".16" = mul i32 %".12", %".15"
  ret i32 %".16"
}

define i32 @"main"()
{
main_entry:
  %".2" = call i32 @"factorial"(i32 5)
  ret i32 %".2"
}
