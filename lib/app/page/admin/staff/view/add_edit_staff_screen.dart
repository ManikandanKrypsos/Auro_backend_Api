import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:aura/app/widgets/custom_textform_lables.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../theme/color/color.dart';
import '../../../../widgets/app_drop_down.dart';
import '../../../../widgets/profile_add_widget.dart';
import '../cubit/staff_manage_cubit.dart';
import '../domain/model/staff_availabilty_model.dart';

class AddEditStaffScreen extends StatefulWidget {
  final bool isEdit;
  const AddEditStaffScreen({super.key, this.isEdit = false});

  @override
  State<AddEditStaffScreen> createState() => _AddEditStaffScreenState();
}

class _AddEditStaffScreenState extends State<AddEditStaffScreen> {
  final _nameCtrl = TextEditingController();
  final _specialistCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _joiningDateCtrl = TextEditingController();
    final _experienceCtrl = TextEditingController();

  @override
  void dispose() {
    _nameCtrl.dispose();
    _specialistCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _joiningDateCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => StaffManageCubit(),
      child: Scaffold(
        backgroundColor: ColorResources.blackColor,
        // AppBar
        appBar: CustomAppBar(
          title: widget.isEdit ? 'EDIT STAFF' : 'ADD NEW STAFF',
        ),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: BlocBuilder<StaffManageCubit, StaffManageState>(
              builder: (context, state) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── Avatar ─────────────────────────────
                    const Center(child: ProfileAddWidget()),
                    const SizedBox(height: 32),

                    // ── Full Name ──────────────────────────
                    const CustomLabel(text: 'FULL NAME'),
                    CustomTextField(
                      controller: _nameCtrl,
                      hint: 'e.g. Julianna Veldt',
                    ),
                    const SizedBox(height: 20),

                    // ── Role ───────────────────────────────
                    const CustomLabel(text: 'SELECT ROLE'),
                    AppDropdown(
                      value: state.selectedRole,
                      items: const ['Therapist', 'Receptionist'],
                      onChanged: (v) {
                        if (v != null)
                          context.read<StaffManageCubit>().selectRole(v);
                      },
                    ),
                    const SizedBox(height: 20),

                    // ── Specialist Area ────────────────────
                    const CustomLabel(text: 'SPECIALIST AREA'),
                    CustomTextField(
                      controller: _specialistCtrl,
                      hint: 'e.g. Medical Aesthetician',
                    ),
                    const SizedBox(height: 20),

                    // ── Email ──────────────────────────────
                    const CustomLabel(text: 'EMAIL ADDRESS'),
                    CustomTextField(
                      controller: _emailCtrl,
                      hint: 'e.g. staff@auraclinic.com',
                    ),
                    const SizedBox(height: 20),

                    // ── Phone ──────────────────────────────
                    const CustomLabel(text: 'PHONE NUMBER'),
                    CustomTextField(
                      controller: _phoneCtrl,
                      hint: 'e.g. +1 (555) 000-0000',
                    ),
                    const SizedBox(height: 20),

                    // ── Joining Date ───────────────────────
                    const CustomLabel(text: 'JOINING DATE'),
                    CustomTextField(
                      controller: _joiningDateCtrl,
                      hint: 'e.g. April 24 2024',
                    ),
                     const SizedBox(height: 20),

                    // ── Joining Date ───────────────────────
                  const CustomLabel(text: 'YEAR OF EXPERIENCE'),
CustomTextField(
  controller: _experienceCtrl,
  hint: '6 years',
),
                    const SizedBox(height: 28),

                    // ── Availability (Therapist only) ──────
                    if (state.selectedRole == 'Therapist') ...[
                      _AvailabilitySection(),
                      const SizedBox(height: 28),
                    ],

                    // Button at the bottom
                    PrimaryButton(
                      label: widget.isEdit
                          ? 'UPDATE STAFF MEMBER'
                          : 'ADD STAFF MEMBER',
                      onTap: () {},
                    ),
                    const SizedBox(height: 40),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}

// ── AVAILABILITY SECTION ────────────────────────────────────
class _AvailabilitySection extends StatelessWidget {
  const _AvailabilitySection();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<StaffManageCubit, StaffManageState>(
      builder: (context, state) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Collapsible header ─────────────────────
            GestureDetector(
              onTap: () =>
                  context.read<StaffManageCubit>().toggleAvailability(),
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 14,
                ),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.calendar_month_outlined,
                      color: ColorResources.primaryColor,
                      size: 16,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'THERAPIST AVAILABILITY',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2.5,
                        ),
                      ),
                    ),
                    AnimatedRotation(
                      turns: state.availabilityExpanded ? 0.5 : 0,
                      duration: const Duration(milliseconds: 200),
                      child: Icon(
                        Icons.keyboard_arrow_down,
                        color: ColorResources.primaryColor,
                        size: 20,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ── Expanded content ───────────────────────
            AnimatedCrossFade(
              duration: const Duration(milliseconds: 250),
              crossFadeState: state.availabilityExpanded
                  ? CrossFadeState.showSecond
                  : CrossFadeState.showFirst,
              firstChild: const SizedBox(width: double.infinity),
              secondChild: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 16),

                  // ── Working Days & Hours ─────────────
                  _SectionLabel(label: 'WORKING DAYS & HOURS'),
                  const SizedBox(height: 12),
                  ...state.weekSchedule.entries.map((entry) {
                    return _DayRow(day: entry.key, schedule: entry.value);
                  }),

                  const SizedBox(height: 24),

                  // ── Break Time ───────────────────────
                  _SectionLabel(label: 'GLOBAL BREAK TIME'),
                  const SizedBox(height: 12),
                  _BreakTimeRow(),

                  const SizedBox(height: 24),

                  // ── Leave Management ─────────────────
                  _SectionLabel(label: 'LEAVE MANAGEMENT'),
                  const SizedBox(height: 12),
                  _LeaveSection(),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}

// ── SECTION LABEL ───────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String label;
  const _SectionLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(width: 2, height: 12, color: ColorResources.primaryColor),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.primaryColor,
            fontSize: 10,
            fontWeight: FontWeight.w600,
            letterSpacing: 2.5,
          ),
        ),
      ],
    );
  }
}

// ── DAY ROW ─────────────────────────────────────────────────
class _DayRow extends StatelessWidget {
  final String day;
  final DaySchedule schedule;
  const _DayRow({required this.day, required this.schedule});

  String _formatTime(TimeOfDay t) {
    final h = t.hourOfPeriod == 0 ? 12 : t.hourOfPeriod;
    final m = t.minute.toString().padLeft(2, '0');
    final period = t.period == DayPeriod.am ? 'AM' : 'PM';
    return '$h:$m $period';
  }

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<StaffManageCubit>();

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          // Day toggle
          GestureDetector(
            onTap: () => cubit.toggleDay(day),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 44,
              height: 36,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: schedule.enabled
                    ? ColorResources.primaryColor.withOpacity(0.12)
                    : Colors.transparent,
                border: Border.all(
                  color: schedule.enabled
                      ? ColorResources.primaryColor
                      : ColorResources.borderColor,
                  width: 0.5,
                ),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                day,
                style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: schedule.enabled
                      ? ColorResources.primaryColor
                      : ColorResources.liteTextColor,
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 1,
                ),
              ),
            ),
          ),

          const SizedBox(width: 10),

          // Time pickers — only show when day is enabled
          Expanded(
            child: AnimatedCrossFade(
              duration: const Duration(milliseconds: 200),
              crossFadeState: schedule.enabled
                  ? CrossFadeState.showSecond
                  : CrossFadeState.showFirst,
              firstChild: Container(
                height: 36,
                alignment: Alignment.centerLeft,
                padding: const EdgeInsets.only(left: 10),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'Day off',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor,
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              ),
              secondChild: Row(
                children: [
                  // Start time
                  Expanded(
                    child: _TimePicker(
                      label: _formatTime(schedule.startTime),
                      onTap: () async {
                        final t = await showTimePicker(
                          context: context,
                          initialTime: schedule.startTime,
                          builder: _timePickerTheme,
                        );
                        if (t != null) cubit.setDayStartTime(day, t);
                      },
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 6),
                    child: Text(
                      '–',
                      style: TextStyle(
                        color: ColorResources.liteTextColor,
                        fontSize: 14,
                      ),
                    ),
                  ),
                  // End time
                  Expanded(
                    child: _TimePicker(
                      label: _formatTime(schedule.endTime),
                      onTap: () async {
                        final t = await showTimePicker(
                          context: context,
                          initialTime: schedule.endTime,
                          builder: _timePickerTheme,
                        );
                        if (t != null) cubit.setDayEndTime(day, t);
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── BREAK TIME ROW ──────────────────────────────────────────
class _BreakTimeRow extends StatelessWidget {
  const _BreakTimeRow();

  String _formatTime(TimeOfDay t) {
    final h = t.hourOfPeriod == 0 ? 12 : t.hourOfPeriod;
    final m = t.minute.toString().padLeft(2, '0');
    final period = t.period == DayPeriod.am ? 'AM' : 'PM';
    return '$h:$m $period';
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<StaffManageCubit, StaffManageState>(
      buildWhen: (p, c) =>
          p.breakStart != c.breakStart || p.breakEnd != c.breakEnd,
      builder: (context, state) {
        final cubit = context.read<StaffManageCubit>();
        return Row(
          children: [
            Expanded(
              child: _TimePicker(
                label: _formatTime(state.breakStart),
                onTap: () async {
                  final t = await showTimePicker(
                    context: context,
                    initialTime: state.breakStart,
                    builder: _timePickerTheme,
                  );
                  if (t != null) cubit.setBreakStart(t);
                },
              ),
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: Text(
                '–',
                style: TextStyle(
                  color: ColorResources.liteTextColor,
                  fontSize: 14,
                ),
              ),
            ),
            Expanded(
              child: _TimePicker(
                label: _formatTime(state.breakEnd),
                onTap: () async {
                  final t = await showTimePicker(
                    context: context,
                    initialTime: state.breakEnd,
                    builder: _timePickerTheme,
                  );
                  if (t != null) cubit.setBreakEnd(t);
                },
              ),
            ),
          ],
        );
      },
    );
  }
}

// ── TIME PICKER TILE ────────────────────────────────────────
class _TimePicker extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  const _TimePicker({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 36,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.access_time_rounded,
              size: 13,
              color: ColorResources.primaryColor,
            ),
            const SizedBox(width: 5),
            Text(
              label,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 12,
                letterSpacing: 0.5,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── LEAVE SECTION ───────────────────────────────────────────
class _LeaveSection extends StatelessWidget {
  const _LeaveSection();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<StaffManageCubit, StaffManageState>(
      buildWhen: (p, c) => p.leaves != c.leaves,
      builder: (context, state) {
        return Column(
          children: [
            // Existing leaves list
            ...state.leaves.asMap().entries.map((e) {
              final i = e.key;
              final leave = e.value;
              final fmt = DateFormat('MMM d, yyyy');
              return Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 12,
                ),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.event_busy_outlined,
                      size: 14,
                      color: ColorResources.primaryColor,
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${fmt.format(leave.from)}  –  ${fmt.format(leave.to)}',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.whiteColor,
                              fontSize: 13,
                              letterSpacing: 0.5,
                            ),
                          ),
                          if (leave.reason.isNotEmpty) ...[
                            const SizedBox(height: 3),
                            Text(
                              leave.reason,
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: ColorResources.liteTextColor,
                                fontSize: 11,
                                fontStyle: FontStyle.italic,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    GestureDetector(
                      onTap: () =>
                          context.read<StaffManageCubit>().removeLeave(i),
                      child: Icon(
                        Icons.close,
                        size: 16,
                        color: ColorResources.liteTextColor,
                      ),
                    ),
                  ],
                ),
              );
            }),

            // Add leave button
            GestureDetector(
              onTap: () => _showAddLeaveSheet(context),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: ColorResources.primaryColor,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.add,
                      size: 14,
                      color: ColorResources.primaryColor,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      'ADD LEAVE',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 2.5,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showAddLeaveSheet(BuildContext context) {
    final cubit = context.read<StaffManageCubit>();
    DateTime? fromDate;
    DateTime? toDate;
    final reasonCtrl = TextEditingController();
    final fmt = DateFormat('MMM d, yyyy');

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF111111),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      isScrollControlled: true,
      builder: (_) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 24,
                right: 24,
                top: 24,
                bottom: MediaQuery.of(ctx).viewInsets.bottom + 32,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Handle
                  Center(
                    child: Container(
                      width: 36,
                      height: 3,
                      decoration: BoxDecoration(
                        color: ColorResources.borderColor,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  Text(
                    'ADD LEAVE',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 16,
                      fontWeight: FontWeight.w300,
                      letterSpacing: 3,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Date range row
                  Row(
                    children: [
                      // From
                      Expanded(
                        child: GestureDetector(
                          onTap: () async {
                            final d = await showDatePicker(
                              context: ctx,
                              initialDate: DateTime.now(),
                              firstDate: DateTime.now(),
                              lastDate: DateTime.now().add(
                                const Duration(days: 365),
                              ),
                              builder: _datePickerTheme,
                            );
                            if (d != null) setSheetState(() => fromDate = d);
                          },
                          child: _DateTile(
                            label: 'FROM',
                            value: fromDate != null
                                ? fmt.format(fromDate!)
                                : null,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      // To
                      Expanded(
                        child: GestureDetector(
                          onTap: () async {
                            final d = await showDatePicker(
                              context: ctx,
                              initialDate: fromDate ?? DateTime.now(),
                              firstDate: fromDate ?? DateTime.now(),
                              lastDate: DateTime.now().add(
                                const Duration(days: 365),
                              ),
                              builder: _datePickerTheme,
                            );
                            if (d != null) setSheetState(() => toDate = d);
                          },
                          child: _DateTile(
                            label: 'TO',
                            value: toDate != null ? fmt.format(toDate!) : null,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Reason
                  TextField(
                    controller: reasonCtrl,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 14,
                    ),
                    decoration: InputDecoration(
                      hintText: 'Reason (optional)',
                      hintStyle: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor,
                        fontSize: 14,
                        fontStyle: FontStyle.italic,
                      ),
                      enabledBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide(
                          color: ColorResources.borderColor,
                          width: 0.5,
                        ),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide(
                          color: ColorResources.primaryColor,
                          width: 0.5,
                        ),
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 12,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Confirm button
                  GestureDetector(
                    onTap: () {
                      if (fromDate != null && toDate != null) {
                        cubit.addLeave(
                          LeaveEntry(
                            from: fromDate!,
                            to: toDate!,
                            reason: reasonCtrl.text.trim(),
                          ),
                        );
                        Navigator.pop(ctx);
                      }
                    },
                    child: Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: ColorResources.primaryColor,
                          width: 0.5,
                        ),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        'CONFIRM LEAVE',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.primaryColor,
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2.5,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}

// ── DATE TILE ───────────────────────────────────────────────
class _DateTile extends StatelessWidget {
  final String label;
  final String? value;
  const _DateTile({required this.label, this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      decoration: BoxDecoration(
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.primaryColor,
              fontSize: 9,
              fontWeight: FontWeight.w600,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value ?? 'Select date',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: value != null
                  ? ColorResources.whiteColor
                  : ColorResources.liteTextColor,
              fontSize: 13,
              fontStyle: value == null ? FontStyle.italic : FontStyle.normal,
            ),
          ),
        ],
      ),
    );
  }
}

// ── SHARED THEME BUILDERS ───────────────────────────────────
Widget _timePickerTheme(BuildContext context, Widget? child) {
  return Theme(
    data: ThemeData.dark().copyWith(
      colorScheme: ColorScheme.dark(
        primary: ColorResources.primaryColor,
        surface: const Color(0xFF111111),
        onSurface: ColorResources.whiteColor,
      ),
      timePickerTheme: TimePickerThemeData(
        backgroundColor: const Color(0xFF111111),
        dialBackgroundColor: const Color(0xFF1A1A1A),
        hourMinuteColor: const Color(0xFF1A1A1A),
        helpTextStyle: TextStyle(
          color: ColorResources.primaryColor,
          letterSpacing: 2,
          fontSize: 11,
        ),
      ),
    ),
    child: child!,
  );
}

Widget _datePickerTheme(BuildContext context, Widget? child) {
  return Theme(
    data: ThemeData.dark().copyWith(
      colorScheme: ColorScheme.dark(
        primary: ColorResources.primaryColor,
        surface: const Color(0xFF111111),
        onSurface: ColorResources.whiteColor,
      ),
      dialogBackgroundColor: const Color(0xFF111111),
    ),
    child: child!,
  );
}
