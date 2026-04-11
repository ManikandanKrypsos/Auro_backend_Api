part of 'staff_manage_cubit.dart';

class StaffManageState {
  final String selectedRole;
  final bool availabilityExpanded;
  final Map<String, DaySchedule> weekSchedule;
  final TimeOfDay breakStart;
  final TimeOfDay breakEnd;
  final List<LeaveEntry> leaves;

  const StaffManageState({
    this.selectedRole = 'Receptionist',
    this.availabilityExpanded = false,
    this.weekSchedule = const {
      'Mon': DaySchedule(),
      'Tue': DaySchedule(),
      'Wed': DaySchedule(),
      'Thu': DaySchedule(),
      'Fri': DaySchedule(),
      'Sat': DaySchedule(),
      'Sun': DaySchedule(),
    },
    this.breakStart = const TimeOfDay(hour: 13, minute: 0),
    this.breakEnd = const TimeOfDay(hour: 14, minute: 0),
    this.leaves = const [],
  });

  StaffManageState copyWith({
    String? selectedRole,
    bool? availabilityExpanded,
    Map<String, DaySchedule>? weekSchedule,
    TimeOfDay? breakStart,
    TimeOfDay? breakEnd,
    List<LeaveEntry>? leaves,
  }) {
    return StaffManageState(
      selectedRole: selectedRole ?? this.selectedRole,
      availabilityExpanded: availabilityExpanded ?? this.availabilityExpanded,
      weekSchedule: weekSchedule ?? this.weekSchedule,
      breakStart: breakStart ?? this.breakStart,
      breakEnd: breakEnd ?? this.breakEnd,
      leaves: leaves ?? this.leaves,
    );
  }
}
