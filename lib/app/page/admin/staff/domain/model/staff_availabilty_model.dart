import 'package:flutter/material.dart';

class LeaveEntry {
  final DateTime from;
  final DateTime to;
  final String reason;

  LeaveEntry({required this.from, required this.to, required this.reason});
}

class DaySchedule {
  final bool enabled;
  final TimeOfDay startTime;
  final TimeOfDay endTime;

  const DaySchedule({
    this.enabled = false,
    this.startTime = const TimeOfDay(hour: 9, minute: 0),
    this.endTime = const TimeOfDay(hour: 17, minute: 0),
  });

  DaySchedule copyWith({bool? enabled, TimeOfDay? startTime, TimeOfDay? endTime}) {
    return DaySchedule(
      enabled: enabled ?? this.enabled,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
    );
  }
}