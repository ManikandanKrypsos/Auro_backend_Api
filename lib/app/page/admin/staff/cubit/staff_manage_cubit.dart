import 'package:bloc/bloc.dart';
import 'package:flutter/material.dart';

import '../domain/model/staff_availabilty_model.dart';

part 'staff_manage_state.dart';



class StaffManageCubit extends Cubit<StaffManageState> {
  StaffManageCubit() : super(const StaffManageState());

  void selectRole(String role) => emit(state.copyWith(selectedRole: role));

  void toggleAvailability() =>
      emit(state.copyWith(availabilityExpanded: !state.availabilityExpanded));

  void toggleDay(String day) {
    final updated = Map<String, DaySchedule>.from(state.weekSchedule);
    updated[day] = updated[day]!.copyWith(enabled: !updated[day]!.enabled);
    emit(state.copyWith(weekSchedule: updated));
  }

  void setDayStartTime(String day, TimeOfDay time) {
    final updated = Map<String, DaySchedule>.from(state.weekSchedule);
    updated[day] = updated[day]!.copyWith(startTime: time);
    emit(state.copyWith(weekSchedule: updated));
  }

  void setDayEndTime(String day, TimeOfDay time) {
    final updated = Map<String, DaySchedule>.from(state.weekSchedule);
    updated[day] = updated[day]!.copyWith(endTime: time);
    emit(state.copyWith(weekSchedule: updated));
  }

  void setBreakStart(TimeOfDay time) =>
      emit(state.copyWith(breakStart: time));

  void setBreakEnd(TimeOfDay time) =>
      emit(state.copyWith(breakEnd: time));

  void addLeave(LeaveEntry leave) =>
      emit(state.copyWith(leaves: [...state.leaves, leave]));

  void removeLeave(int index) {
    final updated = List<LeaveEntry>.from(state.leaves)..removeAt(index);
    emit(state.copyWith(leaves: updated));
  }
}