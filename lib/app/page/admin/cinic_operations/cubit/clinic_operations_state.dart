part of 'clinic_operations_cubit.dart';


class ClinicDaySchedule {
  final bool enabled;
  final TimeOfDay openTime;
  final TimeOfDay closeTime;

  const ClinicDaySchedule({
    this.enabled = false,
    this.openTime = const TimeOfDay(hour: 9, minute: 0),
    this.closeTime = const TimeOfDay(hour: 18, minute: 0),
  });

  ClinicDaySchedule copyWith({
    bool? enabled,
    TimeOfDay? openTime,
    TimeOfDay? closeTime,
  }) {
    return ClinicDaySchedule(
      enabled: enabled ?? this.enabled,
      openTime: openTime ?? this.openTime,
      closeTime: closeTime ?? this.closeTime,
    );
  }
}

class ClinicClosure {
  final DateTime from;
  final DateTime to;
  final String reason;

  const ClinicClosure({
    required this.from,
    required this.to,
    required this.reason,
  });
}

class ClinicOperationsState {
  final Map<String, ClinicDaySchedule> weekSchedule;
  final List<ClinicClosure> closures;

  const ClinicOperationsState({
    this.weekSchedule = const {
      'Mon': ClinicDaySchedule(enabled: true),
      'Tue': ClinicDaySchedule(enabled: true),
      'Wed': ClinicDaySchedule(enabled: true),
      'Thu': ClinicDaySchedule(enabled: true),
      'Fri': ClinicDaySchedule(enabled: true),
      'Sat': ClinicDaySchedule(enabled: false),
      'Sun': ClinicDaySchedule(enabled: false),
    },
    this.closures = const [],
  });

  ClinicOperationsState copyWith({
    Map<String, ClinicDaySchedule>? weekSchedule,
    List<ClinicClosure>? closures,
  }) {
    return ClinicOperationsState(
      weekSchedule: weekSchedule ?? this.weekSchedule,
      closures: closures ?? this.closures,
    );
  }
}
