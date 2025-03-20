; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare i64 @"printf"(i8* %".1", ...)

@"true" = constant i1 1
@"false" = constant i1 0
define i64 @"powi"(i64 %".1", i64 %".2")
{
powi_entry:
  %".4" = alloca i64
  store i64 %".1", i64* %".4"
  %".6" = alloca i64
  store i64 %".2", i64* %".6"
  %".8" = alloca i64
  store i64 1, i64* %".8"
  %".10" = alloca i64
  store i64 0, i64* %".10"
  br label %"for_loop_entry_1"
for_loop_entry_1:
  %".13" = load i64, i64* %".4"
  %".14" = load i64, i64* %".8"
  %".15" = mul i64 %".14", %".13"
  store i64 %".15", i64* %".8"
  %".17" = load i64, i64* %".10"
  %".18" = add i64 %".17", 1
  store i64 %".18", i64* %".10"
  %".20" = load i64, i64* %".10"
  %".21" = load i64, i64* %".6"
  %".22" = icmp slt i64 %".20", %".21"
  br i1 %".22", label %"for_loop_entry_1", label %"for_loop_otherwise_1"
for_loop_otherwise_1:
  %".24" = load i64, i64* %".8"
  ret i64 %".24"
}

define float @"powf"(float %".1", i64 %".2")
{
powf_entry:
  %".4" = alloca float
  store float %".1", float* %".4"
  %".6" = alloca i64
  store i64 %".2", i64* %".6"
  %".8" = alloca float
  store float 0x3ff0000000000000, float* %".8"
  %".10" = alloca i64
  store i64 0, i64* %".10"
  br label %"for_loop_entry_2"
for_loop_entry_2:
  %".13" = load float, float* %".4"
  %".14" = load float, float* %".8"
  %".15" = fmul float %".14", %".13"
  store float %".15", float* %".8"
  %".17" = load i64, i64* %".10"
  %".18" = add i64 %".17", 1
  store i64 %".18", i64* %".10"
  %".20" = load i64, i64* %".10"
  %".21" = load i64, i64* %".6"
  %".22" = icmp slt i64 %".20", %".21"
  br i1 %".22", label %"for_loop_entry_2", label %"for_loop_otherwise_2"
for_loop_otherwise_2:
  %".24" = load float, float* %".8"
  ret float %".24"
}

define i64 @"absi"(i64 %".1")
{
absi_entry:
  %".3" = alloca i64
  store i64 %".1", i64* %".3"
  %".5" = load i64, i64* %".3"
  %".6" = icmp slt i64 %".5", 0
  br i1 %".6", label %"absi_entry.if", label %"absi_entry.endif"
absi_entry.if:
  %".8" = load i64, i64* %".3"
  %".9" = mul i64 %".8", -1
  ret i64 %".9"
absi_entry.endif:
  %".11" = load i64, i64* %".3"
  ret i64 %".11"
}

define float @"absf"(float %".1")
{
absf_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = fcmp olt float %".5",              0x0
  br i1 %".6", label %"absf_entry.if", label %"absf_entry.endif"
absf_entry.if:
  %".8" = load float, float* %".3"
  %".9" = fmul float %".8", 0xbff0000000000000
  ret float %".9"
absf_entry.endif:
  %".11" = load float, float* %".3"
  ret float %".11"
}

@"pi" = constant float 0x400921fb60000000
@"tau" = constant float 0x401921fb60000000
@"e" = constant float 0x4005bf0a80000000
define float @"sqrt"(float %".1")
{
sqrt_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = fcmp olt float %".5",              0x0
  br i1 %".6", label %"sqrt_entry.if", label %"sqrt_entry.endif"
sqrt_entry.if:
  %".8" = fmul float 0x3ff0000000000000, 0xbff0000000000000
  ret float %".8"
sqrt_entry.endif:
  %".10" = load float, float* %".3"
  %".11" = alloca float
  store float %".10", float* %".11"
  %".13" = alloca float
  store float 0x3ff0000000000000, float* %".13"
  %".15" = alloca float
  store float 0x3ee4f8b580000000, float* %".15"
  %".17" = load float, float* %".11"
  %".18" = load float, float* %".13"
  %".19" = fsub float %".17", %".18"
  %".20" = call float @"absf"(float %".19")
  %".21" = load float, float* %".15"
  %".22" = fcmp ogt float %".20", %".21"
  br i1 %".22", label %"while_loop_entry_3", label %"while_loop_otherwise_3"
while_loop_entry_3:
  %".24" = load float, float* %".11"
  %".25" = load float, float* %".13"
  %".26" = fadd float %".24", %".25"
  %".27" = fdiv float %".26", 0x4000000000000000
  %".28" = load float, float* %".11"
  store float %".27", float* %".11"
  %".30" = load float, float* %".3"
  %".31" = load float, float* %".11"
  %".32" = fdiv float %".30", %".31"
  %".33" = load float, float* %".13"
  store float %".32", float* %".13"
  %".35" = load float, float* %".11"
  %".36" = load float, float* %".13"
  %".37" = fsub float %".35", %".36"
  %".38" = call float @"absf"(float %".37")
  %".39" = load float, float* %".15"
  %".40" = fcmp ogt float %".38", %".39"
  br i1 %".40", label %"while_loop_entry_3", label %"while_loop_otherwise_3"
while_loop_otherwise_3:
  %".42" = load float, float* %".11"
  ret float %".42"
}

define float @"ln"(float %".1")
{
ln_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = fcmp ole float %".5",              0x0
  br i1 %".6", label %"ln_entry.if", label %"ln_entry.endif"
ln_entry.if:
  br label %"ln_entry.endif"
ln_entry.endif:
  %".9" = load float, float* %".3"
  %".10" = fsub float %".9", 0x3ff0000000000000
  %".11" = load float, float* %".3"
  %".12" = fadd float %".11", 0x3ff0000000000000
  %".13" = fdiv float %".10", %".12"
  %".14" = alloca float
  store float %".13", float* %".14"
  %".16" = alloca float
  store float              0x0, float* %".16"
  %".18" = load float, float* %".14"
  %".19" = alloca float
  store float %".18", float* %".19"
  %".21" = load float, float* %".14"
  %".22" = load float, float* %".14"
  %".23" = fmul float %".21", %".22"
  %".24" = alloca float
  store float %".23", float* %".24"
  %".26" = alloca i64
  store i64 1, i64* %".26"
  br label %"for_loop_entry_4"
for_loop_entry_4:
  %".29" = load float, float* %".19"
  %".30" = load i64, i64* %".26"
  %".31" = sitofp i64 %".30" to float
  %".32" = fdiv float %".29", %".31"
  %".33" = load float, float* %".16"
  %".34" = fadd float %".33", %".32"
  store float %".34", float* %".16"
  %".36" = load float, float* %".24"
  %".37" = load float, float* %".19"
  %".38" = fmul float %".37", %".36"
  store float %".38", float* %".19"
  %".40" = load i64, i64* %".26"
  %".41" = add i64 %".40", 2
  store i64 %".41", i64* %".26"
  %".43" = load i64, i64* %".26"
  %".44" = icmp slt i64 %".43", 20
  br i1 %".44", label %"for_loop_entry_4", label %"for_loop_otherwise_4"
for_loop_otherwise_4:
  %".46" = load float, float* %".16"
  %".47" = fmul float %".46", 0x4000000000000000
  ret float %".47"
}

define float @"exp"(float %".1")
{
exp_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = alloca float
  store float 0x3ff0000000000000, float* %".5"
  %".7" = alloca float
  store float 0x3ff0000000000000, float* %".7"
  %".9" = alloca i64
  store i64 1, i64* %".9"
  br label %"for_loop_entry_5"
for_loop_entry_5:
  %".12" = load float, float* %".3"
  %".13" = load i64, i64* %".9"
  %".14" = sitofp i64 %".13" to float
  %".15" = fdiv float %".12", %".14"
  %".16" = load float, float* %".7"
  %".17" = fmul float %".16", %".15"
  store float %".17", float* %".7"
  %".19" = load float, float* %".7"
  %".20" = load float, float* %".5"
  %".21" = fadd float %".20", %".19"
  store float %".21", float* %".5"
  %".23" = load i64, i64* %".9"
  %".24" = add i64 %".23", 1
  store i64 %".24", i64* %".9"
  %".26" = load i64, i64* %".9"
  %".27" = icmp slt i64 %".26", 20
  br i1 %".27", label %"for_loop_entry_5", label %"for_loop_otherwise_5"
for_loop_otherwise_5:
  %".29" = load float, float* %".5"
  ret float %".29"
}

define float @"log10"(float %".1")
{
log10_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = call float @"ln"(float %".5")
  %".7" = call float @"ln"(float 0x4024000000000000)
  %".8" = fdiv float %".6", %".7"
  ret float %".8"
}

define float @"log_base"(float %".1", float %".2")
{
log_base_entry:
  %".4" = alloca float
  store float %".1", float* %".4"
  %".6" = alloca float
  store float %".2", float* %".6"
  %".8" = load float, float* %".4"
  %".9" = call float @"ln"(float %".8")
  %".10" = load float, float* %".6"
  %".11" = call float @"ln"(float %".10")
  %".12" = fdiv float %".9", %".11"
  ret float %".12"
}

define float @"sin"(float %".1")
{
sin_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = alloca float
  store float %".5", float* %".6"
  %".8" = load float, float* %".3"
  %".9" = alloca float
  store float %".8", float* %".9"
  %".11" = load float, float* %".3"
  %".12" = load float, float* %".3"
  %".13" = fmul float %".11", %".12"
  %".14" = alloca float
  store float %".13", float* %".14"
  %".16" = alloca i64
  store i64 3, i64* %".16"
  br label %"for_loop_entry_6"
for_loop_entry_6:
  %".19" = load float, float* %".14"
  %".20" = fmul float %".19", 0xbff0000000000000
  %".21" = load i64, i64* %".16"
  %".22" = sub i64 %".21", 1
  %".23" = load i64, i64* %".16"
  %".24" = mul i64 %".22", %".23"
  %".25" = sitofp i64 %".24" to float
  %".26" = fdiv float %".20", %".25"
  %".27" = load float, float* %".9"
  %".28" = fmul float %".27", %".26"
  store float %".28", float* %".9"
  %".30" = load float, float* %".9"
  %".31" = load float, float* %".6"
  %".32" = fadd float %".31", %".30"
  store float %".32", float* %".6"
  %".34" = load i64, i64* %".16"
  %".35" = add i64 %".34", 2
  store i64 %".35", i64* %".16"
  %".37" = load i64, i64* %".16"
  %".38" = icmp slt i64 %".37", 15
  br i1 %".38", label %"for_loop_entry_6", label %"for_loop_otherwise_6"
for_loop_otherwise_6:
  %".40" = load float, float* %".6"
  ret float %".40"
}

define float @"cos"(float %".1")
{
cos_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = alloca float
  store float 0x3ff0000000000000, float* %".5"
  %".7" = alloca float
  store float 0x3ff0000000000000, float* %".7"
  %".9" = load float, float* %".3"
  %".10" = load float, float* %".3"
  %".11" = fmul float %".9", %".10"
  %".12" = alloca float
  store float %".11", float* %".12"
  %".14" = alloca i64
  store i64 2, i64* %".14"
  br label %"for_loop_entry_7"
for_loop_entry_7:
  %".17" = load float, float* %".12"
  %".18" = fmul float %".17", 0xbff0000000000000
  %".19" = load i64, i64* %".14"
  %".20" = sub i64 %".19", 1
  %".21" = load i64, i64* %".14"
  %".22" = mul i64 %".20", %".21"
  %".23" = sitofp i64 %".22" to float
  %".24" = fdiv float %".18", %".23"
  %".25" = load float, float* %".7"
  %".26" = fmul float %".25", %".24"
  store float %".26", float* %".7"
  %".28" = load float, float* %".7"
  %".29" = load float, float* %".5"
  %".30" = fadd float %".29", %".28"
  store float %".30", float* %".5"
  %".32" = load i64, i64* %".14"
  %".33" = add i64 %".32", 2
  store i64 %".33", i64* %".14"
  %".35" = load i64, i64* %".14"
  %".36" = icmp slt i64 %".35", 14
  br i1 %".36", label %"for_loop_entry_7", label %"for_loop_otherwise_7"
for_loop_otherwise_7:
  %".38" = load float, float* %".5"
  ret float %".38"
}

define float @"tan"(float %".1")
{
tan_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = call float @"sin"(float %".5")
  %".7" = load float, float* %".3"
  %".8" = call float @"cos"(float %".7")
  %".9" = fdiv float %".6", %".8"
  ret float %".9"
}

define float @"deg_to_rad"(float %".1")
{
deg_to_rad_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = load float, float* @"pi"
  %".7" = fdiv float %".6", 0x4066800000000000
  %".8" = fmul float %".5", %".7"
  ret float %".8"
}

define float @"rad_to_deg"(float %".1")
{
rad_to_deg_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = load float, float* @"pi"
  %".7" = fdiv float 0x4066800000000000, %".6"
  %".8" = fmul float %".5", %".7"
  ret float %".8"
}

define float @"sin_add"(float %".1", float %".2")
{
sin_add_entry:
  %".4" = alloca float
  store float %".1", float* %".4"
  %".6" = alloca float
  store float %".2", float* %".6"
  %".8" = load float, float* %".4"
  %".9" = call float @"sin"(float %".8")
  %".10" = load float, float* %".6"
  %".11" = call float @"cos"(float %".10")
  %".12" = fmul float %".9", %".11"
  %".13" = load float, float* %".4"
  %".14" = call float @"cos"(float %".13")
  %".15" = load float, float* %".6"
  %".16" = call float @"sin"(float %".15")
  %".17" = fmul float %".14", %".16"
  %".18" = fadd float %".12", %".17"
  ret float %".18"
}

define float @"cos_add"(float %".1", float %".2")
{
cos_add_entry:
  %".4" = alloca float
  store float %".1", float* %".4"
  %".6" = alloca float
  store float %".2", float* %".6"
  %".8" = load float, float* %".4"
  %".9" = call float @"cos"(float %".8")
  %".10" = load float, float* %".6"
  %".11" = call float @"cos"(float %".10")
  %".12" = fmul float %".9", %".11"
  %".13" = load float, float* %".4"
  %".14" = call float @"sin"(float %".13")
  %".15" = load float, float* %".6"
  %".16" = call float @"sin"(float %".15")
  %".17" = fmul float %".14", %".16"
  %".18" = fsub float %".12", %".17"
  ret float %".18"
}

define float @"tan_add"(float %".1", float %".2")
{
tan_add_entry:
  %".4" = alloca float
  store float %".1", float* %".4"
  %".6" = alloca float
  store float %".2", float* %".6"
  %".8" = load float, float* %".4"
  %".9" = call float @"tan"(float %".8")
  %".10" = load float, float* %".6"
  %".11" = call float @"tan"(float %".10")
  %".12" = fadd float %".9", %".11"
  %".13" = load float, float* %".4"
  %".14" = call float @"tan"(float %".13")
  %".15" = load float, float* %".6"
  %".16" = call float @"tan"(float %".15")
  %".17" = fmul float %".14", %".16"
  %".18" = sitofp i64 1 to float
  %".19" = fsub float %".18", %".17"
  %".20" = fdiv float %".12", %".19"
  ret float %".20"
}

define float @"asin"(float %".1")
{
asin_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = alloca float
  store float %".5", float* %".6"
  %".8" = load float, float* %".3"
  %".9" = alloca float
  store float %".8", float* %".9"
  %".11" = load float, float* %".3"
  %".12" = load float, float* %".3"
  %".13" = fmul float %".11", %".12"
  %".14" = alloca float
  store float %".13", float* %".14"
  %".16" = alloca i64
  store i64 1, i64* %".16"
  br label %"for_loop_entry_8"
for_loop_entry_8:
  %".19" = load float, float* %".14"
  %".20" = load i64, i64* %".16"
  %".21" = mul i64 2, %".20"
  %".22" = sub i64 %".21", 1
  %".23" = sitofp i64 %".22" to float
  %".24" = fmul float %".19", %".23"
  %".25" = load i64, i64* %".16"
  %".26" = mul i64 2, %".25"
  %".27" = sitofp i64 %".26" to float
  %".28" = fdiv float %".24", %".27"
  %".29" = load float, float* %".9"
  %".30" = fmul float %".29", %".28"
  store float %".30", float* %".9"
  %".32" = load float, float* %".9"
  %".33" = load i64, i64* %".16"
  %".34" = mul i64 2, %".33"
  %".35" = add i64 %".34", 1
  %".36" = sitofp i64 %".35" to float
  %".37" = fdiv float %".32", %".36"
  %".38" = load float, float* %".6"
  %".39" = fadd float %".38", %".37"
  store float %".39", float* %".6"
  %".41" = load i64, i64* %".16"
  %".42" = add i64 %".41", 1
  store i64 %".42", i64* %".16"
  %".44" = load i64, i64* %".16"
  %".45" = icmp slt i64 %".44", 10
  br i1 %".45", label %"for_loop_entry_8", label %"for_loop_otherwise_8"
for_loop_otherwise_8:
  %".47" = load float, float* %".6"
  ret float %".47"
}

define float @"acos"(float %".1")
{
acos_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* @"pi"
  %".6" = fdiv float %".5", 0x4000000000000000
  %".7" = load float, float* %".3"
  %".8" = call float @"asin"(float %".7")
  %".9" = fsub float %".6", %".8"
  ret float %".9"
}

define float @"atan"(float %".1")
{
atan_entry:
  %".3" = alloca float
  store float %".1", float* %".3"
  %".5" = load float, float* %".3"
  %".6" = call float @"absf"(float %".5")
  %".7" = sitofp i64 1 to float
  %".8" = fcmp ole float %".6", %".7"
  br i1 %".8", label %"atan_entry.if", label %"atan_entry.endif"
atan_entry.if:
  %".10" = load float, float* %".3"
  %".11" = load float, float* %".3"
  %".12" = load float, float* %".3"
  %".13" = fmul float %".11", %".12"
  %".14" = fadd float 0x3ff0000000000000, %".13"
  %".15" = call float @"sqrt"(float %".14")
  %".16" = fdiv float %".10", %".15"
  %".17" = call float @"asin"(float %".16")
  ret float %".17"
atan_entry.endif:
  %".19" = load float, float* @"pi"
  %".20" = fdiv float %".19", 0x4000000000000000
  %".21" = load float, float* %".3"
  %".22" = load float, float* %".3"
  %".23" = fmul float %".21", %".22"
  %".24" = fadd float 0x3ff0000000000000, %".23"
  %".25" = call float @"sqrt"(float %".24")
  %".26" = fdiv float 0x3ff0000000000000, %".25"
  %".27" = call float @"asin"(float %".26")
  %".28" = fsub float %".20", %".27"
  ret float %".28"
}

define i64 @"factorial"(i64 %".1")
{
factorial_entry:
  %".3" = alloca i64
  store i64 %".1", i64* %".3"
  %".5" = load i64, i64* %".3"
  %".6" = icmp eq i64 %".5", 0
  %".7" = load i64, i64* %".3"
  %".8" = icmp eq i64 %".7", 0
  %".9" = or i1 %".6", %".8"
  br i1 %".9", label %"factorial_entry.if", label %"factorial_entry.endif"
factorial_entry.if:
  ret i64 1
factorial_entry.endif:
  %".12" = load i64, i64* %".3"
  %".13" = load i64, i64* %".3"
  %".14" = sub i64 %".13", 1
  %".15" = call i64 @"factorial"(i64 %".14")
  %".16" = mul i64 %".12", %".15"
  ret i64 %".16"
}

define i64 @"main"()
{
main_entry:
  %".2" = load float, float* @"pi"
  %".3" = alloca [5 x i8]*
  store [5 x i8]* @"__str_9", [5 x i8]** %".3"
  %".5" = fpext float %".2" to double
  %".6" = bitcast [5 x i8]* @"__str_9" to i8*
  %".7" = call i64 (i8*, ...) @"printf"(i8* %".6", double %".5")
  %".8" = alloca [14 x i8]*
  store [14 x i8]* @"__str_10", [14 x i8]** %".8"
  %".10" = bitcast [14 x i8]* @"__str_10" to i8*
  %".11" = call i64 (i8*, ...) @"printf"(i8* %".10")
  ret i64 0
}

@"__str_9" = internal constant [5 x i8] c"%f\0a\00\00"
@"__str_10" = internal constant [14 x i8] c"Hello, World!\00"