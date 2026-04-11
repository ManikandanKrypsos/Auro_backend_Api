import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import '../../../../theme/color/color.dart';
import '../cubit/clinic_operations_cubit.dart';

class ClinicOperationsScreen extends StatelessWidget {
  const ClinicOperationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ClinicOperationsCubit(),
      child: Scaffold(
        backgroundColor: ColorResources.blackColor,
        appBar: CustomAppBar(title: 'CLINIC OPERATIONS'),
        body: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: BlocBuilder<ClinicOperationsCubit, ClinicOperationsState>(
              builder: (context, state) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // ── Intro line ─────────────────────────
                    Text(
                      'Configure your clinic\'s weekly schedule and manage planned closures.',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor,
                        fontSize: 14,
                        fontStyle: FontStyle.italic,
                        height: 1.6,
                      ),
                    ),

                    const SizedBox(height: 32),

                    // ── Section: Clinic Hours ───────────────
                    const _SectionHeader(label: 'CLINIC HOURS'),
                    const SizedBox(height: 16),
                    const _ClinicHoursCard(),

                    const SizedBox(height: 32),

                    // ── Section: Closures ───────────────────
                    const _SectionHeader(label: 'PLANNED CLOSURES'),
                    const SizedBox(height: 16),
                    const _ClosuresCard(),

                    const SizedBox(height: 40),

                    // ── Save ────────────────────────────────
                    PrimaryButton(
                      label: 'SAVE CHANGES',
                      onTap: () {
                        // TODO: wire to API
                      },
                    ),

                    const SizedBox(height: 32),
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

// ── SECTION HEADER ──────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final String label;
  const _SectionHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.whiteColor,
        fontSize: 12,
        fontWeight: FontWeight.w600,
        letterSpacing: 3.5,
      ),
    );
  }
}

// ── CLINIC HOURS CARD ───────────────────────────────────────
class _ClinicHoursCard extends StatelessWidget {
  const _ClinicHoursCard();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ClinicOperationsCubit, ClinicOperationsState>(
      builder: (context, state) {
        final entries = state.weekSchedule.entries.toList();
        return Column(
          children: entries.map((e) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: _DayRow(day: e.key, schedule: e.value),
            );
          }).toList(),
        );
      },
    );
  }
}

// ── DAY ROW ─────────────────────────────────────────────────
class _DayRow extends StatelessWidget {
  final String day;
  final ClinicDaySchedule schedule;

  const _DayRow({required this.day, required this.schedule});

  String _fmt(TimeOfDay t) {
    final h = t.hourOfPeriod == 0 ? 12 : t.hourOfPeriod;
    final m = t.minute.toString().padLeft(2, '0');
    final p = t.period == DayPeriod.am ? 'AM' : 'PM';
    return '$h:$m $p';
  }

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<ClinicOperationsCubit>();
    final isEnabled = schedule.enabled;

    return AnimatedContainer(
      duration: const Duration(milliseconds: 250),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: isEnabled
            ? ColorResources.cardColor
            : ColorResources.cardColor.withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isEnabled
              ? ColorResources.primaryColor.withOpacity(0.2)
              : ColorResources.borderColor,
          width: 0.5,
        ),
      ),
      child: Row(
        children: [

          // ── Day badge ─────────────────────────────
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 44,
                height: 44,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: isEnabled
                      ? ColorResources.primaryColor.withOpacity(0.1)
                      : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: isEnabled
                        ? ColorResources.primaryColor.withOpacity(0.35)
                        : ColorResources.borderColor,
                    width: 0.5,
                  ),
                ),
                child: Text(
                  day.substring(0, 3).toUpperCase(),
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: isEnabled
                        ? ColorResources.primaryColor
                        : ColorResources.liteTextColor.withOpacity(0.3),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.8,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(width: 14),

          // ── Times or CLOSED pill ───────────────────
          Expanded(
            child: AnimatedCrossFade(
              duration: const Duration(milliseconds: 220),
              crossFadeState: isEnabled
                  ? CrossFadeState.showSecond
                  : CrossFadeState.showFirst,
              firstChild: Align(
                alignment: Alignment.centerLeft,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    border: Border.all(
                        color: ColorResources.borderColor, width: 0.5),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    'CLOSED',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.4),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),
                ),
              ),
              secondChild: Row(
                children: [
                  _LabeledTimeTile(
                    label: 'OPEN',
                    time: _fmt(schedule.openTime),
                    onTap: () async {
                      final t = await showTimePicker(
                        context: context,
                        initialTime: schedule.openTime,
                        builder: _timePickerTheme,
                      );
                      if (t != null) cubit.setOpenTime(day, t);
                    },
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Text(
                      '→',
                      style: TextStyle(
                        color: ColorResources.primaryColor.withOpacity(0.4),
                        fontSize: 14,
                      ),
                    ),
                  ),
                  _LabeledTimeTile(
                    label: 'CLOSE',
                    time: _fmt(schedule.closeTime),
                    onTap: () async {
                      final t = await showTimePicker(
                        context: context,
                        initialTime: schedule.closeTime,
                        builder: _timePickerTheme,
                      );
                      if (t != null) cubit.setCloseTime(day, t);
                    },
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(width: 12),

          // ── Toggle ────────────────────────────────
          GestureDetector(
            onTap: () => cubit.toggleDay(day),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              width: 40,
              height: 22,
              padding: const EdgeInsets.all(2),
              decoration: BoxDecoration(
                color: isEnabled
                    ? ColorResources.primaryColor.withOpacity(0.15)
                    : Colors.transparent,
                border: Border.all(
                  color: isEnabled
                      ? ColorResources.primaryColor
                      : ColorResources.borderColor,
                  width: 0.8,
                ),
                borderRadius: BorderRadius.circular(12),
              ),
              child: AnimatedAlign(
                duration: const Duration(milliseconds: 220),
                alignment: isEnabled
                    ? Alignment.centerRight
                    : Alignment.centerLeft,
                child: Container(
                  width: 16,
                  height: 16,
                  decoration: BoxDecoration(
                    color: isEnabled
                        ? ColorResources.primaryColor
                        : ColorResources.borderColor,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── LABELED TIME TILE ────────────────────────────────────────
class _LabeledTimeTile extends StatelessWidget {
  final String label;
  final String time;
  final VoidCallback onTap;
  const _LabeledTimeTile({
    required this.label,
    required this.time,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.black,
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
                color: ColorResources.primaryColor.withOpacity(0.7),
                fontSize: 9,
                fontWeight: FontWeight.w700,
                letterSpacing: 2,
              ),
            ),
            const SizedBox(height: 3),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.access_time_rounded,
                  size: 10,
                  color: ColorResources.primaryColor.withOpacity(0.5),
                ),
                const SizedBox(width: 4),
                Text(
                  time,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 13,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}



// ── CLOSURES CARD ───────────────────────────────────────────
class _ClosuresCard extends StatelessWidget {
  const _ClosuresCard();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ClinicOperationsCubit, ClinicOperationsState>(
      buildWhen: (p, c) => p.closures != c.closures,
      builder: (context, state) {
        return Column(
          children: [
            // ── Existing closures ──────────────────────
            if (state.closures.isNotEmpty)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                decoration: BoxDecoration(
                  color: ColorResources.cardColor,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 0.5,
                  ),
                ),
                child: Column(
                  children: state.closures.asMap().entries.map((e) {
                    final isLast = e.key == state.closures.length - 1;
                    return _ClosureRow(
                      closure: e.value,
                      index: e.key,
                      isLast: isLast,
                    );
                  }).toList(),
                ),
              ),

            // ── Add closure button ─────────────────────
            GestureDetector(
              onTap: () => _showAddClosureSheet(context),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  border: Border.all(
                    color: ColorResources.primaryColor,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.add,
                      size: 14,
                      color: ColorResources.primaryColor,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'ADD CLOSURE',
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

  void _showAddClosureSheet(BuildContext context) {
    final cubit = context.read<ClinicOperationsCubit>();
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

                  // Title
                  Text(
                    'ADD CLOSURE',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 18,
                      fontWeight: FontWeight.w300,
                      letterSpacing: 3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Clinic will be marked unavailable for bookings during this period.',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor.withOpacity(0.3),
                      fontSize: 13,
                      fontStyle: FontStyle.italic,
                      height: 1.5,
                    ),
                  ),

                  const SizedBox(height: 24),

                  // Date range
                  Row(
                    children: [
                      Expanded(
                        child: GestureDetector(
                          onTap: () async {
                            final d = await showDatePicker(
                              context: ctx,
                              initialDate: DateTime.now(),
                              firstDate: DateTime.now(),
                              lastDate: DateTime.now().add(
                                const Duration(days: 730),
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
                      Expanded(
                        child: GestureDetector(
                          onTap: () async {
                            final d = await showDatePicker(
                              context: ctx,
                              initialDate: fromDate ?? DateTime.now(),
                              firstDate: fromDate ?? DateTime.now(),
                              lastDate: DateTime.now().add(
                                const Duration(days: 730),
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
                      hintText: 'Reason  e.g. National Holiday',
                      hintStyle: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.liteTextColor,
                        fontSize: 13,
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
                        vertical: 14,
                      ),
                    ),
                  ),

                  const SizedBox(height: 28),

                  // Confirm
                  GestureDetector(
                    onTap: () {
                      if (fromDate != null && toDate != null) {
                        cubit.addClosure(
                          ClinicClosure(
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
                      padding: const EdgeInsets.symmetric(vertical: 15),
                      decoration: BoxDecoration(
                        border: Border.all(
                          color: ColorResources.primaryColor,
                          width: 0.5,
                        ),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text(
                        'CONFIRM CLOSURE',
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

// ── CLOSURE ROW ─────────────────────────────────────────────
class _ClosureRow extends StatelessWidget {
  final ClinicClosure closure;
  final int index;
  final bool isLast;

  const _ClosureRow({
    required this.closure,
    required this.index,
    required this.isLast,
  });

  @override
  Widget build(BuildContext context) {
    final fmt = DateFormat('MMM d, yyyy');

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Date + reason
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${fmt.format(closure.from)}  –  ${fmt.format(closure.to)}',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 14,
                        letterSpacing: 0.3,
                      ),
                    ),
                    if (closure.reason.isNotEmpty) ...[
                      const SizedBox(height: 3),
                      Text(
                        closure.reason,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 12,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),

              // Delete
              GestureDetector(
                onTap: () =>
                    context.read<ClinicOperationsCubit>().removeClosure(index),
                child: Padding(
                  padding: const EdgeInsets.only(left: 8),
                  child: Icon(
                    Icons.close,
                    size: 15,
                    color: ColorResources.liteTextColor,
                  ),
                ),
              ),
            ],
          ),
        ),
        if (!isLast) Container(height: 0.5, color: ColorResources.borderColor),
      ],
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
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
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
          const SizedBox(height: 5),
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
